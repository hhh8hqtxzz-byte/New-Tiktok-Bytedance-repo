# CapCut APK Reverse Engineering + Brute Force Report

## APK Analysis Summary

| Property | Value |
|----------|-------|
| **APK** | CapCut v17.7.0 (com.lemon.lvoverseas) |
| **Version Code** | 17700200 |
| **APK Size** | 108 MB |
| **DEX Files** | 27 (classes.dex through classes27.dex) |
| **Total Strings** | 1,154,185 (43 MB dump) |

## Extraction Results

| Category | Count | TikTok (for ref) | Lemon8 (for ref) |
|----------|-------|-------------------|-------------------|
| Passport endpoints | **190** | 276 | 137 |
| OTP endpoints | **52** | — | 12 |
| API hosts | **34** | 102 | 61 |
| Domains | **138** | 446 | 334 |
| x-tt-* headers | **57** | 73 | 48 |

## KEY DISCOVERY: CapCut Dedicated Passport Infrastructure

CapCut has its own passport backend — separate from tiktokv.com!

| Host | Status | SUCCESSes |
|------|--------|-----------|
| `passport-api.capcut.com` | **SUCCESS** | AID=1583, 6027, 2239, 1760 |
| `passport-api.capcutapi.com` | **SUCCESS** | AID=1583, 6027 |
| `passport-api-va-us-looki.capcutapi.com` | **SUCCESS** | AID=6027 |
| `passport-api-v2-boot.capcutapi.com` | **SUCCESS** | AID=2239 |
| `tt-passport16-normal-sg.capcutapi.com` | **SUCCESS** | AID=6027, 1760 |

### Additional API Hosts from CapCut APK
| Host | Purpose |
|------|---------|
| `api-boot.tiktokv.com` | **SUCCESS** (AID=2239) |
| `inapp.tiktokv.com` | **SUCCESS** (AID=6027) |
| `api16-core-c-alisg.tiktokv.com` | Core API |
| `api22-core-c-alisg.tiktokv.com` | Core API |
| `api.capcut.com` | General API |
| `api-sg.capcut.com` | SG region API |
| `api.capcutapi.com` | API v2 |

### CapCut-Specific Sub-Domains
- `editor-api.capcut.com` / `editor-api-va.capcutapi.com`
- `feed-api.capcut.com` / `feed-api-sg.capcut.com`
- `commerce-api.capcutapi.com`
- `general-api-us-looki.capcutapi.com`
- `sf-fe.capcut.com` (frontend)

---

## Brute Force v5.0 Results

### Phase Summary

| Phase | Tests | Description | Key Results |
|-------|-------|-------------|-------------|
| **A** | 320 | CapCut passport hosts × ALL 32 AIDs | 5 SUCCESSes, 113 RL |
| **B** | 640 | CapCut sub-API + tiktokv.com hosts × ALL AIDs | 1 SUCCESS (inapp.tiktokv.com) |
| **C** | 756 | NEW endpoints (sms_login_continue, chain_login) | 10 RL on new endpoints |
| **D** | 2,325 | Verify + expand | 11 SUCCESSes confirming all findings |
| **Total** | **~5,041** | | **15 SUCCESSes + 317 rate-limited** |

### All 15 CONFIRMED SUCCESSes

| AID | App | Domain | TC | Phase |
|-----|-----|--------|----|-------|
| 1583 | TikTok Ads | passport-api.capcut.com | 3635 | A |
| 6027 | BD 6027 | passport-api.capcut.com | 3635 | A |
| 6027 | BD 6027 | passport-api-va-us-looki.capcutapi.com | 3635 | A |
| 6027 | BD 6027 | tt-passport16-normal-sg.capcutapi.com | 3635 | A |
| 1760 | BD 1760 | tt-passport16-normal-sg.capcutapi.com | 3635 | A |
| 6027 | BD 6027 | inapp.tiktokv.com | 3634 | B |
| 1583 | TikTok Ads | passport-api.capcutapi.com | 3635 | D |
| 6027 | BD 6027 | passport-api.capcutapi.com | 3733 | D |
| 6027 | BD 6027 | passport-api.capcutapi.com | 3635 | D |
| 6027 | BD 6027 | passport-api-va-us-looki.capcutapi.com | 3733 | D |
| 2239 | BD 2239 | passport-api-v2-boot.capcutapi.com | 3734 | D |
| 2239 | BD 2239 | passport-api.capcut.com | 3734 | D |
| 2239 | BD 2239 | passport-api-v2-boot.capcutapi.com | 3635 | D |
| 1760 | BD 1760 | passport-api.capcut.com | 3635 | D |
| 2239 | BD 2239 | api-boot.tiktokv.com | 3635 | D |

### New Apps Added to /setapp2

| Key | AID | Name | # Domains | # TCs |
|-----|-----|------|-----------|-------|
| `bd6027_capcut` | 6027 | BD 6027 CapCut | 5 | 3 |
| `bd1583_capcut` | 1583 | TikTok Ads CapCut | 4 | 3 |
| `bd2239_capcut` | 2239 | BD 2239 CapCut | 3 | 3 |
| `bd1760_capcut` | 1760 | BD 1760 CapCut | 2 | 3 |

### New Endpoints Found (52 OTP-related in CapCut APK)
- `/passport/mobile/sms_login_continue/` — **NEW** (rate-limited = valid)
- `/passport/mobile/can_chain_login/` — **NEW** (rate-limited = valid)
- `/passport/mobile/chain_login/` — **NEW** (rate-limited = valid)
- `/passport/web/email/send_code/` — web email OTP
- `/passport/email/login/` — email login endpoint
- `/passport/email/register/v2/` — v2 register
- `/passport/org/account/permission/role/invite/send_code/` — org invitation!

---

## Bot v15.0 Domain Lists

| List | Count | New |
|------|-------|-----|
| CAPCUT_PASSPORT_DOMAINS | **5** | NEW |
| CAPCUT_TIKTOKV_HOSTS | **5** | NEW |
| Total CONFIRMED_APPS | **28** | +4 |
