# TikTok APK — Reverse Engineering & Endpoints Report

**APK:** `com.zhiliaoapp.musically` (TikTok Global)
**Version:** 45.0.42 (versionCode `2024500420`) — latest as of April 2025
**APK Size:** 364 MB
**DEX Files:** 50 (`classes.dex` … `classes50.dex`, total ~400 MB compiled code)
**Decompile Method:** DEX strings extraction (`strings -a -n 6` on all 50 DEX files → 2.28M strings, 48 MB)
**Strings file:** `all_strings.txt` (48 MB)

---

## 1. Passport Endpoints (`/passport/...`) — 276 unique paths

### 1.1 OTP / Verification Endpoints (KEY for our bot)

| # | Endpoint | Already in bot? |
|---|----------|-----------------|
| 1 | `/passport/mobile/send_code/v1/` | YES |
| 2 | `/passport/mobile/send_code/` | YES |
| 3 | `/passport/web/send_code/` | YES |
| 4 | `/passport/email/send_code/` | YES (email-only) |
| 5 | `/passport/web/email/send_code/` | NEW — web email |
| 6 | `/passport/mobile/send_voice_code/` | YES |
| 7 | `/passport/mobile/can_send_voice_code/` | NEW — pre-check before voice |
| 8 | `/passport/mobile/check_code/` | NEW — verify SMS OTP |
| 9 | `/passport/mobile/validate_code/v1/` | NEW — alt verify |
| 10 | `/passport/mobile/validate_code/` | NEW — alt verify |
| 11 | `/passport/email/check_code/` | NEW — verify email OTP |
| 12 | `/passport/web/email/check_code/` | NEW |
| 13 | `/passport/org/account/permission/role/invite/send_code/` | NEW (TikTok for Business org) |

### 1.2 Login Endpoints (use AFTER `send_code`)

```
/passport/mobile/sms_login/
/passport/mobile/sms_login_continue/
/passport/mobile/sms_login_only/
/passport/mobile/login/
/passport/mobile/chain_login/                ← chained multi-step login
/passport/mobile/conditional_bind_login/     ← bind+login one-shot
/passport/mobile/origin_mobile_login/
/passport/mobile/mobile_card_login/          ← carrier auth login
/passport/mobile/mobile_reused_login/        ← reused number login
/passport/mobile/bind_login/
/passport/auth/one_login/
/passport/auth/one_login_by_ticket/
/passport/auth/one_login_continue/
/passport/auth/only_login/
/passport/auth/share_login/                  ← share-based login
/passport/auth/wap_login/                    ← WAP login
/passport/email/login/
/passport/user/login/
/passport/user/login_by_passport_ticket/
/passport/user/login_by_verify_ticket/       ← login after OTP verify
/passport/cloud_token/login/
/passport/oidc/login/
/passport/oidc/multi_login/                  ← multi-account
/passport/recall/bind_ticket_login/
/passport/sso/login/callback/
/passport/carrier_auth/login_continue/
/passport/carrier_auth/login_only/
```

### 1.3 Bind / Change / Register

```
/passport/mobile/bind/
/passport/mobile/bind/v1/
/passport/mobile/bind/v2/
/passport/mobile/bind_for_connect/
/passport/mobile/change/
/passport/mobile/change/v1/
/passport/mobile/register/
/passport/email/register/
/passport/email/register/v2/
/passport/email/register_verify/
/passport/email/register_verify_login/
/passport/email/bind/
/passport/email/bind_and_verify/
/passport/email/bind_email_for_device_login/
/passport/auth/bind_with_mobile/
/passport/auth/bind_with_mobile_login/
/passport/web/mobile/bind/
/passport/web/mobile/bind_with_2sv/
/passport/username/register/
/passport/login_name/register/
```

### 1.4 Account Lookup (PRE-OTP — check if number is registered)

```
/passport/account_lookup/cloud/
/passport/account_lookup/device/
/passport/account_lookup/email/
/passport/account_lookup/mobile/        ← USE THIS BEFORE send_code
/passport/account_lookup/username/
```

### 1.5 Two-Step Verification / Security

```
/passport/safe/two_step_verification/
/passport/safe/two_step_verification/add_auth_device/
/passport/safe/two_step_verification/add_auth_device/v2/
/passport/safe/two_step_verification/add_verification/
/passport/safe/two_step_verification/add_verification/v2/
/passport/safe/two_step_verification/get_auth_device_list/
/passport/safe/two_step_verification/get_verification_list/
/passport/safe/two_step_verification/remove_all/
/passport/safe/two_step_verification/remove_auth_device/
/passport/safe/two_step_verification/remove_verification/
/passport/safe/two_step_verification/remove_verification/v2/
/passport/safe/login_device/list/
/passport/safe/login_device/list/v2/
/passport/safe/login_device/del/
/passport/safe/recommend_device/list/
/passport/totp/
/passport/totp/bind_verify/
/passport/totp/recover/
/passport/totp/register/
/passport/totp/register/v2/
/passport/totp/status/
/passport/totp/update/
/passport/totp/verify/
/passport/totp/verify_without_login/
/passport/fido2/
/passport/fido2/begin_user_authentication/
/passport/fido2/begin_user_registration/
/passport/fido2/begin_discoverable_user_login/
/passport/fido2/credentials/
/passport/fido2/finish_user_authentication/
/passport/fido2/finish_user_registration/
/passport/fido2/finish_discoverable_user_login/
/passport/fido2/remove_credentials/
/passport/shark/safe_verify/
/passport/shark/safe_verify/v2/
/passport/shark/safe_verify/verification_manage/
```

### 1.6 Token / Session

```
/passport/auth/get_nonce/
/passport/auth/get_token/
/passport/token/beat/
/passport/token/beat/v2/
/passport/token/change/
/passport/transfer/get_token/
/passport/cloud_token/disable/
/passport/cloud_token/enable/
```

### 1.7 Account Management

```
/passport/account/info/
/passport/account/info/v2/
/passport/account/set/
/passport/account/switch/
/passport/account/switch/v2/
/passport/account/verify/
/passport/account/attributes/
/passport/account/authorize/
/passport/cancel/confirm/
/passport/cancel/do/
/passport/cancel/login/
/passport/cancel/post/
/passport/deactivation/do/
/passport/deactivation/login/
/passport/deactivation/post/
/passport/region/change/submit/post/
/passport/app/region/
/passport/app/region/register_region_list/
/passport/app/region_alert/
/passport/app/store_region/
```

(Full 276-endpoint list: `apk_findings/passport_endpoints.txt`)

---

## 2. AIDs Found in TikTok APK

Hardcoded references inside JSON config blobs:

| AID | App | Notes |
|-----|-----|-------|
| **1233** | TikTok Global | confirmed (existing) |
| **1180** | Helo | confirmed (existing) |
| **259** | BD 259 | confirmed (existing) |
| **473824** | NEW — TikTok-internal sub-app | not yet in bot |
| **567753** | NEW — TikTok-internal sub-app | not yet in bot |

Discovered context:
```json
"aid": ["473824"]
"aid_not": ["1233", "1180"]
"aid": ["259"]
"aid_not": ["1233", "1180", "259"]
"aid_not": ["1233", "1180", "259", "473824", "567753"]
```

These are AIDs the TikTok app explicitly excludes/includes when applying experiments — meaning ByteDance ships these as **valid app identities**.

---

## 3. API Hosts — 102 unique mobile API endpoints

### 3.1 NEW Hosts NOT in current bot

| Host | Type |
|------|------|
| **api16-normal-useast5.tiktokv.us** | TikTok US — `.tiktokv.us` TLD! |
| **api16-normal-useast8.tiktokv.us** | TikTok US |
| **api19-core-c-useast1a.tiktokv.com** | core variant |
| **api19-core-va.tiktokv.com** | core variant |
| **api19-normal-c-useast1a.tiktokv.com** | NEW |
| **api19-va.tiktokv.com** | NEW |
| **api19.tiktokv.com** | NEW |
| **api21-core-va.tiktokv.com** | NEW |
| **api21-h2-eagle.tiktokv.com** | NEW (h2/eagle infra) |
| **api21-h2.tiktokv.com** | NEW |
| **api21-va.tiktokv.com** | NEW |
| **api21.tiktokv.com** | NEW |
| **api22-h2-eagle.tiktokv.com** | NEW |
| **api22-core-c-alisg.tiktokv.com** | NEW |
| **api22-core-c-useast1a.tiktokv.com** | NEW |
| **api22-va.tiktokv.com** | NEW |
| **api22.tiktokv.com** | NEW |
| **api23-normal-useast1a.tiktokv.com** | NEW |
| **api31-normal-alisg.tiktokv.com** | NEW |
| **api31-normal-useast1a.tiktokv.com** | NEW |
| **api32-normal-alisg.tiktokv.com** | NEW |
| **api32-normal-useast1a.tiktokv.com** | NEW |
| **api-core-boot.tiktokv.com** | boot variant |
| **api-core-va.tiktokv.com** | core variant |
| **api-core.tiktokv.com** | core variant |
| **api-h2-eagle.tiktokv.com** | h2/eagle |
| **api-normal.tiktokv.com** | NEW |
| **hotapi-boot.tiktokv.com** | NEW class — `hotapi.*` |
| **hotapi-sg.tiktokv.com** | NEW |
| **hotapi-va.tiktokv.com** | NEW |
| **hotapi-va.isnssdk.com** | NEW (isnssdk!) |
| **hotapi-va-ueast2a-useast2a.isnssdk.com** | NEW |
| **hotapi16-normal-alisg.tiktokv.com** | NEW |
| **hotapi16-normal-useast1a.tiktokv.com** | NEW |
| **hotapi22-normal-useast1a.tiktokv.com** | NEW |
| **api16-normal-alisg.helo-api.com** | NEW! Helo official API |
| **fp-sg.tiktokv.com** | feature platform SG |
| **fp-va.tiktokv.com** | feature platform VA |
| **fp22-normal-useast1a.tiktokv.com** | NEW |
| **frontier-va.tiktokv.com** | NEW |
| **frontier100-normal.tiktokv.com** | NEW |
| **mssdk-sg.tiktokv.com** / **mssdk-va.tiktokv.com** | mssdk infra |
| **mon.zijieapi.com** | confirmed `zijieapi.com` |
| **client_monitor.isnssdk.com** | new isnssdk subdomain |
| **f-p-va.isnssdk.com** | NEW isnssdk |
| **i.isnssdk.com** | NEW isnssdk |
| **imapi-mu.isnssdk.com** | NEW IM api |
| **imapi-sg.isnssdk.com** | NEW IM api |
| **imapi-16.tiktokv.com** | NEW |
| **logger-va.tiktokv.com** / **logger.tiktokv.us** | logging |
| **location.tiktokv.com** | location lookup |

### 3.2 Domain TLDs Discovered

* `tiktokv.com` (most common)
* `tiktokv.us` ← **NEW TLD!**
* `tiktok.com` (web)
* `tiktokcdn.com` / `tiktokcdn-us.com` (CDN)
* `byteoversea.com`
* `snssdk.com`
* `isnssdk.com` ← **i-prefixed snssdk variant**
* `amemv.com`
* `musical.ly`
* `zijieapi.com`
* `helo-api.com` ← **NEW Helo backend**
* `pipix.com` / `capcutapi.com` (referenced)

(Full 102-host list: `apk_findings/api_hosts.txt`. Full 446-domain list: `apk_findings/domains_clean.txt`.)

---

## 4. ByteDance App Identification

App package: `com.zhiliaoapp.musically`
Compiled: SDK 35 (Android 15), min SDK 23 (Android 6.0)
Embedded Amazon API key (Login with Amazon SDK) ties package: `com.zhiliaoapp.musically`.

---

## 5. HTTP Headers Used by TikTok APK

### 5.1 Signing / Auth (KNOWN — already in bot)
```
X-Gorgon, X-Khronos, X-Argus, X-Ladon
X-Tt-Token, x-tt-token, x-tt-token-appid
X-Tt-Passport-Csrf-Token, x-tt-passport-ticket
```

### 5.2 NEW useful headers we should add to bot

| Header | Purpose |
|--------|---------|
| `x-tt-multi-sids` | Multi-account session IDs |
| `x-tt-cmpl-token` | Compliance token (region-specific) |
| `x-tt-cipher-version` | Cipher protocol version |
| `x-tt-encrypt-info` / `x-tt-encrypt-queries` | Body/query encryption |
| `x-tt-bypass-bdturing` | Bypass captcha/risk check |
| `x-tt-bdturing-retry` | Retry after captcha |
| `x-tt-bp-rs` | Backpressure / rate signal |
| `x-tt-dataflow-id` | Trace ID for ML |
| `x-tt-env` | Environment (prod/staging) |
| `x-tt-app-init-region` | First-install region |
| `x-tt-app-cdn-region` | CDN region |
| `x-tt-store-region` | Already added ✓ |
| `x-tt-store-region-src` | Already added ✓ |
| `x-tt-tnc-config` / `x-tt-tnc-control` / `x-tt-tnc-summary` | Network config |
| `x-tt-cloud-key` / `x-tt-cloud-key-timestamp` / `x-tt-cloud-key-client-data` | Cloud encryption |
| `x-tt-pba-enable` / `x-tt-pba-encode` | Privacy-Bind-Address |
| `x-tt-request-tag` / `x-tt-request-scenario` | Request classifier |
| `x-tt-trace-id` / `X-Tt-Logid` | Tracing |
| `x-tt-traceflag` | Trace flag |
| `X-Wltc-Token` | WLTC token |
| `X-Vc-Bdturing-Sdk-Version` | bdturing version |

73 unique `x-tt-*` headers discovered (full list: `apk_findings/xtt_headers.txt`).

---

## 6. Analysis Summary

* **TikTok 45.0.42 supports 276 distinct passport endpoints** — our bot was using only 5 of them (send_code v1, send_code, web/send_code, email/send_code, send_voice_code). That's only **1.8% coverage**.
* **102 mobile API hosts vs ~26 in our bot** — **76 new hosts** to test (api19-32, hotapi*, fp*, mssdk-*, logger-*, helo-api.com, .tiktokv.us TLD).
* **2 new AIDs (473824, 567753)** hardcoded in TikTok config — undocumented ByteDance internal apps.
* **`hotapi-*` domain class** — completely new endpoint family on both `tiktokv.com` and `isnssdk.com`. Worth testing for `/passport/mobile/send_code/`.
* **`.tiktokv.us` TLD** — separate US infrastructure (`api16-normal-useast5.tiktokv.us`, `api16-normal-useast8.tiktokv.us`). Not tested before.
* **NEW endpoint candidates** — `/passport/mobile/can_send_voice_code/`, `/passport/account_lookup/mobile/`, `/passport/mobile/sms_login/` family, `/passport/mobile/conditional_bind_login/`, etc.

---

## 7. Recommended Next Tests (priority order)

1. **`/passport/account_lookup/mobile/`** — pre-OTP lookup (free intel, may have looser rate limits)
2. **AID 473824 + AID 567753** on `/passport/web/send_code/` and `/passport/mobile/send_code/v1/`
3. **`hotapi-*.tiktokv.com`** + standard send_code (new domain family)
4. **`.tiktokv.us` hosts** with US proxy
5. **`api16-normal-alisg.helo-api.com`** + AID 1180
6. **`/passport/mobile/can_send_voice_code/`** — possibly looser rate-limit gate
7. **`/passport/mobile/conditional_bind_login/`** + `/passport/mobile/chain_login/` flows
8. **Add new headers** (`x-tt-bypass-bdturing`, `x-tt-cmpl-token`, `x-tt-cipher-version`, `x-tt-multi-sids`)

---

## 8. Reproducing this analysis

```bash
# 1. Download
curl -L -o tiktok.apk -A "Mozilla/5.0" \
  "https://d.apkpure.net/b/APK/com.zhiliaoapp.musically?version=latest"

# 2. Extract DEX
unzip -q tiktok.apk "*.dex" -d extracted/

# 3. Strings dump
for f in extracted/classes*.dex; do strings -a -n 6 "$f"; done > all_strings.txt

# 4. Endpoints
grep -oE '/passport/[a-zA-Z0-9_/]+/' all_strings.txt | sort -u > passport_endpoints.txt

# 5. Domains
grep -oE '\b[a-z][a-z0-9_-]*(\.[a-z0-9_-]+)+\.(com|us|ly|cn|net)\b' all_strings.txt \
  | grep -iE 'tiktok|snssdk|amemv|musical|byteoversea|bytedance|capcut|pipix|zijieapi|helo|isnssdk' \
  | sort -u > domains.txt

# 6. AIDs
grep -E '"aid"|aid_not' all_strings.txt | head -50
```
