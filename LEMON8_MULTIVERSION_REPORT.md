# Lemon8 Multi-Version Analysis Report

**Goal:** Achieve SUCCESS on Lemon8 endpoints by analyzing multiple Lemon8 APK versions and brute-force testing all extracted infrastructure.

**Result:** **23 SUCCESSes on Lemon8** across 7 unique domains and 8 different AIDs.

---

## 1. Versions Analyzed (8 total)

| Version | Source | APK Size | DEX Strings |
|---------|--------|----------|-------------|
| v11.8.2 | APKPure XAPK | 76.4 MB | 388,722 |
| v11.9.1 | APKPure XAPK | 76.6 MB | 389,219 |
| v12.0.1 | APKPure XAPK | 43.7 MB | 391,289 |
| v12.1.1 | APKPure XAPK | 76.9 MB | 391,298 |
| v12.2.1 | APKPure XAPK | 76.9 MB | 393,743 |
| v12.3.1 | APKPure XAPK | 77.0 MB | 395,370 |
| v12.4.1 | Existing analysis | 77.1 MB | 396,365 |
| v12.5.1 | APKPure XAPK | 77.1 MB | 400,097 |

Each version was unzipped → DEX files extracted → strings dumped → endpoints/hosts/headers/AIDs extracted using regex.

## 2. Multi-Version Findings

The Lemon8 SDK is shared across all 8 versions — same 142 passport endpoints, same 131 API hosts, same 84 `x-tt-*` headers in every version. **No version-specific deltas in core SDK strings.**

However, Lemon8-DEDICATED hosts not previously tested:

```
lemonapi16-normal-useast5.tiktokv.us       (US East 5 region)
lemonapi16-normal-useast8.tiktokv.us       (US East 8 region — NEW)
lemonapi16-normal-alisg.tiktokv.com        (Alibaba Singapore)
lemonapi16-normal-no1a.tiktokv.eu          (Norway 1a / .eu TLD — NEW)
lemonapi16-normal-useastred.tiktokv.eu     (US East Red / .eu TLD — NEW)
v.lemon8-app.com                           (Video subdomain — NEW)
s.lemon8-app.com                           (Static subdomain — NEW)
api.lemon8-app.com                         (API subdomain)
web.lemon8-app.com                         (Web subdomain — NEW)
```

These are LEMON8-EXCLUSIVE infrastructure. The `tiktokv.eu` TLD with regional suffixes (`no1a`, `useastred`) is brand new.

## 3. Brute Force Results

5-phase brute force across 33 AIDs × Lemon8 hosts × 4 signed + 3 web endpoints × 12 type codes × 15 regions.

**Total: 3,762 tests | 23 SUCCESSes | 451 rate-limited | 161 sec runtime**

### SUCCESS Combos (23 total)

| AID | Domain | Endpoint | Type Codes |
|-----|--------|----------|-----------|
| 1583 | lemonapi16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 3635 |
| 1760 | lemonapi16-normal-useast8.tiktokv.us | /passport/web/send_code/ | 3536 |
| 1988 | lemonapi16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 34 |
| 1988 | lemonapi16-normal-useast8.tiktokv.us | /passport/web/send_code/ | 34, 3132, 3635 |
| 2239 | lemon8-api.tiktokv.com | /passport/web/send_code/ | 3536, 3632 |
| 2239 | lemonapi16-normal-useast8.tiktokv.us | /passport/web/send_code/ | 34 |
| 2239 | s.lemon8-app.com | /passport/web/send_code/ | 3132 |
| 2239 | v.lemon8-app.com | /passport/web/send_code/ | 3631 |
| 4143 | lemonapi16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 3631 |
| 6027 | api.lemon8-app.com | /passport/web/send_code/ | 34 |
| 6849 | lemonapi16-normal-useast5.tiktokv.us | /passport/web/send_code/ | 3536, 3632 |
| 7743 | api.lemon8-app.com | /passport/mobile/send_code/v1/ | 34 |
| 7743 | lemon8-api.tiktokv.com | /passport/mobile/send_code/v1/ | 3536, 3731, 3734 |
| 7743 | lemonapi16-normal-alisg.tiktokv.com | /passport/mobile/send_code/v1/ | 3536 |
| 7743 | lemonapi16-normal-useast5.tiktokv.us | /passport/mobile/send_code/v1/ | 34 |
| 7743 | lemonapi16-normal-useast8.tiktokv.us | /passport/mobile/send_code/v1/ | 3731 |
| 7743 | v.lemon8-app.com | /passport/mobile/send_code/v1/ | 3731 |

**Unique AIDs:** 1583, 1760, 1988, 2239, 4143, 6027, 6849, 7743 (8 AIDs)
**Unique Domains:** 7 dedicated Lemon8 hosts
**Best AID:** 7743 (7 SUCCESSes across 6 domains)

### Phase Breakdown

- **Phase A (Lemon8-Dedicated × Signed Mobile):** 5 SUCCESSes / 1980 tests
- **Phase B (Lemon8 own-domains × Web):** 0 SUCCESSes (web subdomains return non-JSON)
- **Phase C (Lemon8-Dedicated × Web):** 18 SUCCESSes / 1782 tests — **BEST PHASE**
- **Phase D (AID 4370 Laser):** 0 SUCCESSes (Lemon8 official AID — heavily limited)
- **Phase E (AID 2658 Laser):** 0 SUCCESSes (heavily rate-limited)

## 4. Bot.py Updates (v17.0)

Added 8 new CONFIRMED_APPS for `/setapp2`:

```
lemon8_2239_dedicated  (4 domains, 6 type codes)
lemon8_7743_dedicated  (6 domains, 4 type codes)  ← STRONGEST
lemon8_1988_dedicated  (2 domains, 3 type codes)
lemon8_1583_dedicated  (1 domain, 1 type code)
lemon8_1760_dedicated  (1 domain, 1 type code)
lemon8_4143_dedicated  (1 domain, 1 type code)
lemon8_6849_dedicated  (1 domain, 2 type codes)
lemon8_6027_dedicated  (1 domain, 1 type code)
```

Added new domain lists:
- `LEMON8_DEDICATED_DOMAINS` (5 hosts including .eu TLD)
- `LEMON8_WEB_HOSTS` (5 hosts on lemon8-app.com)

CONFIRMED_APPS count: 34 → **42** (8 new Lemon8-dedicated apps).

## 5. Files

- `lemon8_multiversion_bruteforce.py` — reusable brute force script
- `lemon8_multiversion_findings/all_endpoints.txt` — 142 passport endpoints
- `lemon8_multiversion_findings/all_api_hosts.txt` — 130 API hosts
- `lemon8_multiversion_findings/all_lemon8_related_hosts.txt` — 271 Lemon8-related domains
- `lemon8_multiversion_findings/all_headers.txt` — 83 x-tt-* headers
- `lemon8_multiversion_findings/bruteforce_results.json` — full SUCCESS/RL findings
- `lemon8_multiversion_findings/summary.json` — per-version analysis stats
- `lemon8_multiversion_findings/unique_per_version.json` — version-specific deltas

## 6. How to Use

In Telegram bot:

```
/setapp2 → "Lemon8 AID 7743 (Dedicated CONFIRMED)"
```

Then choose a domain (or "All Domains" round-robin) and a type code, and start sending OTPs to Lemon8 numbers.

The strongest pick is `lemon8_7743_dedicated` because it has 6 different working domains for rotation.
