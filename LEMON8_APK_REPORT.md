# Lemon8 APK Reverse Engineering + Combined Brute Force Report

## APK Analysis Summary

| Property | Value |
|----------|-------|
| **APK** | Lemon8 v12.4.1 (com.bd.nproject) |
| **Version Code** | 120401 |
| **APK Size** | 74 MB |
| **DEX Files** | 6 (classes.dex through classes6.dex) |
| **Total Strings** | 396,000+ (9.4 MB dump) |

## Extraction Results

| Category | Count | TikTok APK (for comparison) |
|----------|-------|-----------------------------|
| Passport endpoints | **137** | 276 |
| API hosts | **61** | 102 |
| Domains | **334** | 446 |
| x-tt-* headers | **48** | 73 |
| OTP endpoints | **12** | — |

## NEW Discoveries (Not in TikTok APK)

### api77-* Host Family (4 hosts)
| Host | Status |
|------|--------|
| `api77-normal-c-alisg.tiktokv.com` | RL confirmed (multiple AIDs) |
| `api77-normal-c-useast1a.tiktokv.com` | **SUCCESS** (AID=2239 tc=3634) |
| `api77-core-c-alisg.tiktokv.com` | RL confirmed |
| `api77-core-c-useast1a.tiktokv.com` | RL confirmed |

### Lemon8-Specific Domains
| Domain | Status |
|--------|--------|
| `lemon8-api.tiktokv.com` | **SUCCESS** (AID=2239 tc=3635) |
| `verify-sg.tiktokv.com` | **SUCCESS** (AID=6027 tc=3634, AID=2239 tc=3635) |
| `verify-sg.byteoversea.com` | RL confirmed |

### sgsnssdk.com Family (Lemon8-exclusive infrastructure)
| Domain | Status |
|--------|--------|
| `f-p.sgsnssdk.com` | **SUCCESS** (AID=2239 tc=3634) |
| `hotapi.sgsnssdk.com` | Tested |
| `i.sgsnssdk.com` | Tested |
| `mon.sgsnssdk.com` | Tested |

### Lemon8 App-Specific Domains
- `lemon8-app.com` — Primary Lemon8 domain
- `lemon8cdn.com` — CDN for Lemon8 content
- `lemon8-app.byteoversea.com` — ByteDance overseas Lemon8

---

## Combined Brute Force v4.0 Results

### Phase Summary

| Phase | Tests | Description | Key Results |
|-------|-------|-------------|-------------|
| **A** | ~1,364 | Lemon8 NEW hosts × ALL 31 AIDs | AID=2239 SUCCESS on api77, 24+ RL |
| **B** | ~2,604 | 14 TikTok APK hosts × ALL 31 AIDs | AID=1988/4143 SUCCESS on tiktokv.us, fp-* SUCCESS |
| **C** | ~3,588 | Chinese apps deep scan (6 AIDs × all new hosts) | Chinese apps ec=16 on Lemon8 hosts (expected) |
| **D** | ~1,500+ | Verify + expand | 20+ additional SUCCESSes confirming all findings |
| **Total** | **~9,000+** | | **38 SUCCESSes + 897 rate-limited** |

### All 38 CONFIRMED SUCCESSes

| AID | App | Domain | Endpoint | TC | Phase |
|-----|-----|--------|----------|----|-------|
| 2239 | BD 2239 | api77-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3634 | A |
| 1988 | Douyin Web | api16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 3634 | B |
| 4143 | BD 4143 | api16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 3635 | B |
| 1988 | Douyin Web | api16-normal-useast8.tiktokv.us | /passport/web/send_code/ | 3637 | B |
| 1760 | BD 1760 | fp-va.tiktokv.com | /passport/web/send_code/ | 3734 | B |
| 7743 | BD 7743 | fp22-normal-useast1a.tiktokv.com | /passport/mobile/send_code/v1/ | 3532 | B |
| 1760 | BD 1760 | fp-sg.tiktokv.com | /passport/web/send_code/ | 3734 | B |
| 1760 | BD 1760 | fp22-normal-useast1a.tiktokv.com | /passport/web/send_code/ | 3634 | B |
| 1583 | TikTok Ads | api22-normal-c-alisg.tiktokv.com | /passport/web/send_code/ | 3635 | D |
| 2239 | BD 2239 | api-h2.tiktokv.com | /passport/web/send_code/ | 3634 | D |
| 6027 | BD 6027 | api16-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3635 | D |
| 6027 | BD 6027 | verify-sg.tiktokv.com | /passport/web/send_code/ | 3634 | D |
| 2239 | BD 2239 | lemon8-api.tiktokv.com | /passport/web/send_code/ | 3635 | D |
| 1760 | BD 1760 | api16-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3734 | D |
| 2239 | BD 2239 | verify-sg.tiktokv.com | /passport/web/send_code/ | 3635 | D |
| 1760 | BD 1760 | api-h2.tiktokv.com | /passport/web/send_code/ | 3733 | D |
| 1760 | BD 1760 | verify-sg.tiktokv.com | /passport/web/send_code/ | 3634 | D |
| 1583 | TikTok Ads | api22-normal-c-alisg.tiktokv.com | /passport/web/send_code/ | 3733 | D |
| 1760 | BD 1760 | api16-normal-v4.tiktokv.com | /passport/web/send_code/ | 3637 | D |
| 2239 | BD 2239 | api16-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3634 | D |
| 1760 | BD 1760 | api16-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3637 | D |
| 1760 | BD 1760 | api16-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3634 | D |
| 7743 | BD 7743 | api16-normal-v4.tiktokv.com | /passport/mobile/send_code/v1/ | 3532 | D |
| 7743 | BD 7743 | api-h2.tiktokv.com | /passport/mobile/send_code/v1/ | 3536 | D |
| 7743 | BD 7743 | api-h2.tiktokv.com | /passport/mobile/send_code/v1/ | 3734 | D |
| 1760 | BD 1760 | api16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 3634 | D |
| 2239 | BD 2239 | api16-normal-v4.tiktokv.com | /passport/web/send_code/ | 3734 | D |
| 2239 | BD 2239 | api22-normal-c-alisg.tiktokv.com | /passport/web/send_code/ | 3637 | D |
| 6027 | BD 6027 | api16-normal-v4.tiktokv.com | /passport/web/send_code/ | 3733 | D |
| 1760 | BD 1760 | api16-normal-useast8.tiktokv.us | /passport/web/send_code/ | 3637 | D |
| 2239 | BD 2239 | api16-normal-useast8.tiktokv.us | /passport/web/send_code/ | 3634 | D |
| 2239 | BD 2239 | f-p.sgsnssdk.com | /passport/web/send_code/ | 3634 | D |
| 1760 | BD 1760 | api22-normal-c-alisg.tiktokv.com | /passport/web/send_code/ | 3734 | D |
| 6027 | BD 6027 | api16-normal-c-useast1a.tiktokv.com | /passport/web/send_code/ | 3634 | D |
| 7743 | BD 7743 | api16-normal-c-useast1a.tiktokv.com | /passport/mobile/send_code/v1/ | 3536 | D |
| 7743 | BD 7743 | api22-normal-c-alisg.tiktokv.com | /passport/mobile/send_code/v1/ | 3536 | D |
| 7743 | BD 7743 | api22-normal-c-alisg.tiktokv.com | /passport/mobile/send_code/v1/ | 3731 | D |
| 7743 | BD 7743 | api16-normal-v6.tiktokv.com | /passport/mobile/send_code/v1/ | 3734 | D |

### New Apps Added to /setapp2

| Key | AID | Name | # Domains | # TCs |
|-----|-----|------|-----------|-------|
| `bd2239_s` | 2239 | BD 2239 | 11 | 5 |
| `bd1760_s` | 1760 | BD 1760 | 10 | 5 |
| `bd6027_s` | 6027 | BD 6027 | 5 | 3 |
| `bd4143_s` | 4143 | BD 4143 | 4 | 3 |

### Updated Apps

| App | Changes |
|-----|---------|
| TikTok Ads | +3 domains (api22, api77, lemon8-api), +1 TC |
| Douyin Web | +3 domains (tiktokv.us 8, api77, verify-sg) |
| BD 7743 | +4 domains (fp22, api22, api-h2, api32), +1 TC |
| BD 2658 | +3 domains (fp-va, api-normal, api16-useast1a), +1 TC |

### Bot v14.0 Domain Lists

| List | Count | New |
|------|-------|-----|
| TIKTOKV_MOBILE_DOMAINS | 41 | — |
| LEMON8_API_DOMAINS | **7** | NEW |
| SGSNSSDK_DOMAINS | **4** | NEW |
| FP_DOMAINS | **3** | NEW |
| Total CONFIRMED_APPS | **24** | +4 |
| Total BYTEDANCE_APPS | 30 | — |

---

## Lemon8 APK Extracted Data

### Passport Endpoints (137 total, key ones)
```
/passport/mobile/send_code/v1/
/passport/mobile/send_code/
/passport/web/send_code/
/passport/mobile/can_send_voice_code/
/passport/mobile/send_voice_code/
/passport/mobile/sms_login/v1/
/passport/mobile/sms_login_only/
/passport/mobile/check_code/
/passport/mobile/validate_code/v1/
/passport/account_lookup/mobile/
/passport/open/send_code/
/passport/mobile/change/v1/
```

### API Hosts (61 total, NEW ones highlighted)
```
api77-normal-c-alisg.tiktokv.com        **NEW**
api77-normal-c-useast1a.tiktokv.com     **NEW**
api77-core-c-alisg.tiktokv.com          **NEW**
api77-core-c-useast1a.tiktokv.com       **NEW**
lemon8-api.tiktokv.com                  **NEW** (Lemon8 dedicated!)
verify-sg.tiktokv.com                   **NEW**
verify-sg.byteoversea.com               **NEW**
hotapi.sgsnssdk.com                     **NEW**
f-p.sgsnssdk.com                        **NEW**
i.sgsnssdk.com                          **NEW**
mon.sgsnssdk.com                        **NEW**
```

---

## Methodology
1. Downloaded Lemon8 APK (74 MB, v12.4.1) from APKMirror
2. Extracted 6 DEX files using `unzip`
3. Used `strings` binary to extract all hardcoded strings from DEX bytecode
4. Grep'd for passport endpoints, API hosts, domains, x-tt-* headers
5. Built `lemon8_combined_bruteforce.py` with 4 phases:
   - Phase A: Lemon8 NEW hosts × ALL 31 AIDs
   - Phase B: TikTok APK remaining hosts × ALL 31 AIDs
   - Phase C: Chinese apps deep scan on all new domains
   - Phase D: Verify & expand findings
6. 300+ concurrent workers, multiple proxy regions (AU/DE/SG/US/FR/GB)
