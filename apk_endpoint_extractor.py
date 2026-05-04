#!/usr/bin/env python3
"""
APK Endpoint Extractor
======================

Downloads a TikTok / ByteDance APK, extracts all DEX files, runs `strings`
on them, and dumps:

    apk_findings/
        passport_endpoints.txt   - all /passport/* paths
        otp_endpoints.txt        - send_code/voice_code/check_code subset
        api_hosts.txt            - mobile API hostnames (api*.tiktokv.com etc)
        all_domains.txt          - every ByteDance-related domain
        xtt_headers.txt          - x-tt-* HTTP headers used by the app
        all_strings.txt          - raw strings dump (tens of MB)

Usage:
    python3 apk_endpoint_extractor.py [path/to/app.apk]

If no path given, downloads the latest TikTok APK from APKPure.

Requires: `unzip`, `strings` (binutils), Python 3.8+.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

WORK = Path("apk_analysis_work")
OUT = Path("apk_findings")
APK_DEFAULT_URL = (
    "https://d.apkpure.net/b/APK/com.zhiliaoapp.musically?version=latest"
)

DOMAIN_FAMILIES = (
    "tiktok|snssdk|amemv|musical|byteoversea|bytedance|capcut|pipix|"
    "zijieapi|byteapi|isnssdk|toutiao|byteplus|volcengine|trill|douyin|"
    "jianying|ixigua|helo|lemon8|larksuite|feishu|tiktokv|tiktokcdn"
)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print(f"+ {' '.join(cmd)}")
    return subprocess.run(cmd, check=True, **kw)


def download_apk(url: str, dst: Path) -> None:
    print(f"Downloading {url} -> {dst}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f)
    size_mb = dst.stat().st_size / (1024 * 1024)
    print(f"Downloaded: {size_mb:.1f} MB")


def extract_dex(apk: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    run(["unzip", "-q", "-o", str(apk), "*.dex", "-d", str(dst)])


def dump_strings(dex_dir: Path, out_file: Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "wb") as out:
        for dex in sorted(dex_dir.glob("classes*.dex")):
            print(f"  strings {dex.name}")
            r = subprocess.run(
                ["strings", "-a", "-n", "6", str(dex)],
                stdout=subprocess.PIPE,
                check=True,
            )
            out.write(r.stdout)
    size_mb = out_file.stat().st_size / (1024 * 1024)
    print(f"Strings dump: {size_mb:.1f} MB")


def write_unique(lines: set[str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(lines)) + "\n")
    print(f"  wrote {len(lines):>5} lines -> {path}")


def grep_findings(strings_file: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    re_passport = re.compile(rb"/passport/[a-zA-Z0-9_/]+/")
    re_xtt = re.compile(rb"x-tt-[a-zA-Z0-9_-]+")
    re_domain = re.compile(
        (
            r"\b[a-z][a-z0-9_-]*(\.[a-z0-9_-]+)+"
            r"\.(com|us|ly|cn|net)\b"
        ).encode()
    )
    re_family = re.compile(DOMAIN_FAMILIES.encode())
    re_api_host = re.compile(
        rb"\b(?:api[a-z0-9-]*|hotapi[a-z0-9-]*|imapi[a-z0-9-]*|fp[a-z0-9-]*|"
        rb"jsb[a-z0-9-]*|libra[a-z0-9-]*|log[a-z0-9-]*|gecko[a-z0-9-]*|"
        rb"mon[a-z0-9-]*|frontier[a-z0-9-]*|mssdk[a-z0-9-]*|location|i\.|"
        rb"im-va|client_monitor|verify|aweme|f-p|ib|i-hl|is-hl|is-lq|lf)"
        rb"[\.\w-]*\.(?:tiktokv\.com|tiktokv\.us|snssdk\.com|isnssdk\.com|"
        rb"byteoversea\.com|amemv\.com|musical\.ly|capcut\.com|"
        rb"capcutapi\.com|pipix\.com|zijieapi\.com|helo-api\.com)\b"
    )

    passport: set[str] = set()
    xtt: set[str] = set()
    domains: set[str] = set()
    api_hosts: set[str] = set()

    print("Scanning strings file...")
    with open(strings_file, "rb") as f:
        for raw in f:
            for m in re_passport.findall(raw):
                passport.add(m.decode("ascii", "ignore"))
            for m in re_xtt.findall(raw):
                xtt.add(m.decode("ascii", "ignore"))
            for d in re_domain.finditer(raw):
                d_str = d.group(0).decode("ascii", "ignore")
                if re_family.search(d_str.encode()):
                    domains.add(d_str)
            for h in re_api_host.findall(raw):
                api_hosts.add(h.decode("ascii", "ignore"))

    write_unique(passport, out_dir / "passport_endpoints.txt")
    write_unique(xtt, out_dir / "xtt_headers.txt")
    write_unique(domains, out_dir / "all_domains.txt")
    write_unique(api_hosts, out_dir / "api_hosts.txt")

    otp_keywords = (
        "send_code",
        "send_voice",
        "send_sms",
        "verify_code",
        "send_msg",
        "/sms/",
        "/code/",
        "/voice/",
        "/otp/",
        "verify_ticket",
        "check_code",
    )
    otp = {p for p in passport if any(k in p for k in otp_keywords)}
    write_unique(otp, out_dir / "otp_endpoints.txt")


def main() -> int:
    apk_path = Path(sys.argv[1]) if len(sys.argv) > 1 else WORK / "tiktok.apk"

    WORK.mkdir(parents=True, exist_ok=True)
    if not apk_path.exists():
        download_apk(APK_DEFAULT_URL, apk_path)

    if not apk_path.exists():
        print(f"APK not found: {apk_path}", file=sys.stderr)
        return 1

    dex_dir = WORK / "extracted"
    strings_file = WORK / "all_strings.txt"

    extract_dex(apk_path, dex_dir)
    dump_strings(dex_dir, strings_file)
    grep_findings(strings_file, OUT)

    print("\nDONE. Findings in:", OUT.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
