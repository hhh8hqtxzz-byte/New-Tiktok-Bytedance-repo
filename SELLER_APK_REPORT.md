# TikTok Seller APK Reverse Engineering + Brute Force Report

## APK Analysis Summary

| Property | Value |
|----------|-------|
| **APK** | TikTok Shop Seller Center v10.6.0 (com.tiktokshop.seller) |
| **Version Code** | 100600 |
| **APK Size** | 61 MB |
| **DEX Files** | 7 (classes.dex through classes7.dex) |
| **Total Strings** | 356,276 (11 MB dump) |

## Extraction Results

| Category | Count |
|----------|-------|
| Passport endpoints | **130** |
| OTP endpoints | **40** |
| API hosts | **27** |
| Domains | **114** |
| x-tt-* headers | **48** |

## KEY DISCOVERY: TikTok Shop's Dedicated Infrastructure

### New TLD: `tiktokglobalshopv.com` / `tiktokglobalshopv.us`
TikTok Shop has its own dedicated backend — completely separate from tiktokv.com!

| Host | SUCCESSful AIDs |
|------|-----------------|
| `api.tiktokglobalshopv.com` | **7743, 2239, 1583** |
| `api.tiktokglobalshopv.us` | **7743, 1583, 6849, 1760** |
| `api.eu.tiktokglobalshopv.com` | **6027** |
| `api.row.tiktokglobalshopv.com` | RL confirmed |

### New Verification Hosts
| Host | SUCCESSful AIDs |
|------|-----------------|
| `verification-va.tiktokv.com` | **2239, 6027, 7743** |
| `verification16-normal-useast5.tiktokv.us` | **1760** |
| `rc-verification-va.tiktokv.com` | **2239, 6027** |
| `rc-verification-sg.tiktokv.com` | **2239, 6027, 7743** |
| `rc-verification-i18n.tiktokv.com` | **6027** |
| `rc-verification16-normal-useast5.tiktokv.us` | **7743, 1988, 4143, 1760, 6849** |

### Additional Hosts
| Host | SUCCESSful AIDs |
|------|-----------------|
| `web-va.tiktok.com` | **7743** |
| `ads.tiktok.com` | **2239, 7743** |
| `oec-api.tiktokv.com` | RL confirmed |
| `scc.tiktokv.com` | RL confirmed |

### NEW TLD: `.tiktokv.eu`
- `rc-verification.tiktokv.eu`
- `vcs16-normal-ie.tiktokv.eu`

---

## Brute Force v6.0 Results

| Phase | Tests | Key Results |
|-------|-------|-------------|
| **A** | 624 | tiktokglobalshopv.com/us: 6 SUCCESSes |
| **B** | 1,144 | Verification + ads: 9 SUCCESSes |
| **C** | 312 | isnssdk.com: 0 (timeout issues) |
| **D** | 1,572 | Verify + expand: 44 SUCCESSes |
| **Total** | **~3,652** | **38 unique SUCCESSes + 656 RL** |

### New /setapp2 Apps (6 new)

| Key | AID | # Domains | Highlight |
|-----|-----|-----------|-----------|
| `bd7743_shop` | 7743 | 7 | Most domains of any app! |
| `bd2239_shop` | 2239 | 5 | verification + shop + ads |
| `bd6027_shop` | 6027 | 5 | rc-verification + EU shop |
| `bd6849_shop` | 6849 | 2 | shop.us + rc-verification |
| `bd1760_shop` | 1760 | 3 | verification + shop |
| `bd4143_shop` | 4143 | 1 | rc-verification16 |

---

## Bug Fix: /schedule Command

Fixed `/schedule` (scheduletask) bug where scheduled tasks were ignoring the user's selected app and always using default "pipix".

**Root cause:** `ScheduledTask` dataclass did not store `app_key`, `override_domain`, `override_tc`, or `domain_mode`. When `run_scheduled_task` created a new `Task`, it used the default app_key="pipix".

**Fix:** Added app settings fields to `ScheduledTask`, captured user's current settings in `schedule_command`, and propagated them in `run_scheduled_task`.
