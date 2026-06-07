"""
Test Runner — Invokes the repo's standalone brute-force / fuzzing scripts from
inside the Telegram bot. Patches each script's proxy / phone / concurrency at
runtime so they use the bot's saved proxies + numbers, then streams every
"SUCCESS" / interesting line to chat and finally sends a TXT report.

Bot integration: bot.py's /test command calls run_external_test(...) for any
script registered in TEST_SCRIPTS.
"""

import asyncio
import contextlib
import importlib
import inspect
import io
import json
import os
import random
import re
import sys
import time
from typing import Callable, Dict, List, Optional


# ──────────────────────────────────────────────────────────────────────────
# Registry: short_name -> (module_name, label, description)
# ──────────────────────────────────────────────────────────────────────────
TEST_SCRIPTS: Dict[str, Dict[str, str]] = {
    "apk":         {"mod": "apk_bruteforce",             "label": "APK Brute Force v3",            "desc": "AID 473824/567753 × NEW endpoints/hosts (APK RE)"},
    "capcut":      {"mod": "capcut_combined_bruteforce", "label": "CapCut Combined v5",            "desc": "CapCut endpoints across regions × TCs"},
    "lemon8":      {"mod": "lemon8_combined_bruteforce", "label": "Lemon8 + TikTok Combined v4",   "desc": "Lemon8 endpoints, multi-app"},
    "lemon8v":     {"mod": "lemon8_multiversion_bruteforce", "label": "Lemon8 Multi-Version",      "desc": "Lemon8 across app versions"},
    "seller":      {"mod": "seller_bruteforce",          "label": "TikTok Seller v6",               "desc": "TikTok Seller APK endpoints"},
    "ultra":       {"mod": "ultra_bruteforce",           "label": "Ultra Mega v2",                  "desc": "AID 1-100k + hidden endpoints"},
    "mega":        {"mod": "mega_test",                  "label": "Mega Test",                      "desc": "amemv domains × tc=3532/3635 × all apps"},
    "fuzzer":      {"mod": "mega_fuzzer",                "label": "Mega Fuzzer v1",                 "desc": "Multi-phase fuzzer (NEW AIDs/endpoints/headers)"},
    "volcengine":  {"mod": "volcengine_test",            "label": "Volcengine Test",                "desc": "AID 3569/3559 + verify.zijieapi.com"},
    "domain":      {"mod": "domain_refresh_scan",        "label": "Domain Refresh Scan",            "desc": "Find new working domains for all apps"},
    "aid2658":     {"mod": "aid2658_final",              "label": "AID 2658 Final",                 "desc": "All methods × all regions on AID=2658"},
    "aid2658f":    {"mod": "aid2658_focused",            "label": "AID 2658 Focused",               "desc": "Slow focused attack on AID=2658"},
    "aid":         {"mod": "aid_bruteforce",             "label": "AID Brute Force (web)",          "desc": "AID 1-10k on web endpoint"},
    "signed":      {"mod": "aid_bruteforce_signed",      "label": "AID Brute Force (signed)",       "desc": "AID 1-10k on signed mobile"},
}

# Lines we forward to chat as "HIT" notifications. Order matters — more
# specific patterns first so we don't double-fire on the same line.
HIT_PATTERNS = [
    re.compile(r"\*\*\*\s*SUCCESS\s*\*\*\*", re.I),
    re.compile(r"\[\+\]\s*HIT", re.I),
    re.compile(r"^\s*>>>\s*SUCCESS", re.I),
    re.compile(r"\bsuccessful\b.*\baid=", re.I),
    re.compile(r"\bmsg=['\"]?success['\"]?", re.I),
    re.compile(r"\bSUCCESS\b.*\baid[=:]?\s*\d", re.I),
    re.compile(r"\bFOUND\b.*\b(aid|domain|tc)\b", re.I),
    re.compile(r"breakthrough", re.I),
]

# Lines forwarded as "PROGRESS" (less spammy — every Nth line only)
PROGRESS_PATTERNS = [
    re.compile(r"Phase\s+[A-D]\]", re.I),
    re.compile(r"Progress:\s*\d", re.I),
    re.compile(r"\bSUC[:=]\s*\d", re.I),
]


class _ChatTeeStream(io.TextIOBase):
    """A stdout-replacement that mirrors writes to:
       1. the real stdout (for server-side logs)
       2. an in-memory full transcript (for the TXT file at the end)
       3. an asyncio queue of "interesting" lines (hits / progress)
    """

    def __init__(self, queue: asyncio.Queue, transcript: List[str]):
        super().__init__()
        self._real = sys.__stdout__
        self._queue = queue
        self._transcript = transcript
        self._buf = ""
        self._progress_counter = 0

    def writable(self) -> bool: return True

    def write(self, s: str) -> int:
        if not isinstance(s, str):
            s = str(s)
        try: self._real.write(s)
        except Exception: pass
        self._buf += s
        while "\n" in self._buf or "\r" in self._buf:
            idx_n = self._buf.find("\n"); idx_r = self._buf.find("\r")
            if idx_n == -1: idx = idx_r
            elif idx_r == -1: idx = idx_n
            else: idx = min(idx_n, idx_r)
            line, self._buf = self._buf[:idx], self._buf[idx + 1:]
            line = line.rstrip()
            if not line: continue
            self._transcript.append(line)
            self._classify_and_enqueue(line)
        return len(s)

    def flush(self) -> None:
        try: self._real.flush()
        except Exception: pass

    def _classify_and_enqueue(self, line: str) -> None:
        # Skip ANSI escapes
        clean = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", line)
        for pat in HIT_PATTERNS:
            if pat.search(clean):
                try: self._queue.put_nowait(("hit", clean))
                except asyncio.QueueFull: pass
                return
        for pat in PROGRESS_PATTERNS:
            if pat.search(clean):
                self._progress_counter += 1
                if self._progress_counter % 25 == 1:
                    try: self._queue.put_nowait(("progress", clean))
                    except asyncio.QueueFull: pass
                return


# ──────────────────────────────────────────────────────────────────────────
# Module patching
# ──────────────────────────────────────────────────────────────────────────
def _patch_module(mod, proxies: List[str], numbers: List[str], concurrency: Optional[int]) -> Dict[str, object]:
    """Monkey-patch a script module so it uses bot's saved proxies/numbers.

    Returns a dict of original attributes for later restoration.
    """
    if not proxies:
        raise ValueError("No proxies provided")
    backup: Dict[str, object] = {}

    def _gp(region=None, *a, **kw):
        return random.choice(proxies)

    def _gen_phone(*a, **kw):
        if numbers:
            return random.choice(numbers)
        # fall back to original module function if it existed
        orig = backup.get("_gen_phone_orig")
        if callable(orig):
            return orig()
        return None

    def _get_phone(region=None, *a, **kw):
        if numbers:
            return random.choice(numbers)
        orig = backup.get("_get_phone_orig")
        if callable(orig):
            return orig(region)
        return None

    # Patch proxy supplier
    if hasattr(mod, "get_proxy"):
        backup["get_proxy"] = mod.get_proxy
        mod.get_proxy = _gp
    if hasattr(mod, "PROXY"):
        backup["PROXY"] = mod.PROXY
        mod.PROXY = random.choice(proxies)
    if hasattr(mod, "PROXY_TEMPLATE"):
        backup["PROXY_TEMPLATE"] = mod.PROXY_TEMPLATE

        class _PT(str):
            """A str subclass whose .format() returns a random bot proxy
            regardless of the format args the script passes in."""
            def format(self, *a, **kw):
                return random.choice(proxies)

        mod.PROXY_TEMPLATE = _PT(mod.PROXY_TEMPLATE)

    # Patch phone suppliers (only if user gave numbers)
    if numbers:
        if hasattr(mod, "gen_phone"):
            backup["_gen_phone_orig"] = mod.gen_phone
            backup["gen_phone"] = mod.gen_phone
            mod.gen_phone = _gen_phone
        if hasattr(mod, "get_phone"):
            backup["_get_phone_orig"] = mod.get_phone
            backup["get_phone"] = mod.get_phone
            mod.get_phone = _get_phone
        if hasattr(mod, "fresh_phone"):
            backup["fresh_phone"] = mod.fresh_phone
            mod.fresh_phone = lambda *a, **kw: random.choice(numbers)

    # Patch concurrency / worker constants
    if concurrency:
        for attr in dir(mod):
            if attr.startswith("MAX_CONCURRENT") or attr in (
                "WORKERS", "MAX_WORKERS", "CONCURRENCY", "POOL_SIZE",
            ):
                try:
                    if isinstance(getattr(mod, attr), int):
                        backup[attr] = getattr(mod, attr)
                        setattr(mod, attr, concurrency)
                except Exception:
                    pass

    return backup


def _unpatch_module(mod, backup: Dict[str, object]) -> None:
    """Restore module attributes."""
    for attr, val in backup.items():
        if attr.startswith("_") and attr.endswith("_orig"):
            continue
        try:
            setattr(mod, attr, val)
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────
async def run_external_test(
    short_name: str,
    proxies: List[str],
    numbers: List[str],
    chat_id,
    context,
    concurrency: int = 50,
    max_hits_in_chat: int = 30,
    on_done: Optional[Callable] = None,
) -> Dict:
    """Run one of the registered test scripts, stream hits to chat,
    send a TXT report at the end. Returns a summary dict."""

    info = TEST_SCRIPTS.get(short_name)
    if not info:
        await context.bot.send_message(
            chat_id,
            f"<b>Unknown test mode:</b> {short_name}\n\n"
            "Use /test to see the menu of available modes.",
            parse_mode="HTML",
        )
        return {"ok": False, "error": "unknown_mode"}

    mod_name = info["mod"]
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        await context.bot.send_message(
            chat_id,
            f"<b>Failed to import {mod_name}:</b>\n<code>{str(e)[:300]}</code>",
            parse_mode="HTML",
        )
        return {"ok": False, "error": str(e)}

    # Patch
    try:
        backup = _patch_module(mod, proxies, numbers, concurrency)
    except Exception as e:
        await context.bot.send_message(
            chat_id,
            f"<b>Failed to patch {mod_name}:</b>\n<code>{str(e)[:300]}</code>",
            parse_mode="HTML",
        )
        return {"ok": False, "error": str(e)}

    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
    transcript: List[str] = []
    hits: List[str] = []
    stream = _ChatTeeStream(queue, transcript)

    cancel_event = asyncio.Event()

    # Pump task — drains queue and posts to chat
    async def _pump():
        sent_hits = 0
        sent_progress = 0
        while not cancel_event.is_set():
            try:
                kind, line = await asyncio.wait_for(queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            if kind == "hit":
                hits.append(line)
                if sent_hits < max_hits_in_chat:
                    sent_hits += 1
                    try:
                        await context.bot.send_message(
                            chat_id,
                            f"<b>HIT #{sent_hits}</b>\n<code>{_truncate(line, 380)}</code>",
                            parse_mode="HTML",
                        )
                    except Exception: pass
                elif sent_hits == max_hits_in_chat:
                    sent_hits += 1
                    try:
                        await context.bot.send_message(
                            chat_id,
                            f"... more hits suppressed (full list in final TXT).",
                            parse_mode="HTML",
                        )
                    except Exception: pass
            elif kind == "progress":
                sent_progress += 1
                if sent_progress <= 12:
                    try:
                        await context.bot.send_message(
                            chat_id,
                            f"⏳ <i>{_truncate(line, 200)}</i>",
                            parse_mode="HTML",
                        )
                    except Exception: pass

    pump_task = asyncio.create_task(_pump())

    # Start banner
    try:
        await context.bot.send_message(
            chat_id,
            (f"<b>Test Started: {info['label']}</b>\n"
             f"Mode: <code>/test {short_name}</code>\n"
             f"Module: <code>{mod_name}.py</code>\n"
             f"Proxies: {len(proxies)} | Numbers: {len(numbers) if numbers else 'auto-gen'}\n"
             f"Concurrency: {concurrency}\n\n"
             f"<i>{info['desc']}</i>\n\n"
             f"Hits will stream as they arrive..."),
            parse_mode="HTML",
        )
    except Exception: pass

    start = time.time()
    error_msg: Optional[str] = None
    try:
        # Redirect stdout for the duration of the run
        with contextlib.redirect_stdout(stream):
            print(f"[bot] running {mod_name}.main() with {len(proxies)} bot proxies, "
                  f"{len(numbers)} bot numbers, concurrency={concurrency}")
            main_fn = getattr(mod, "main", None) or getattr(mod, "run", None)
            if not main_fn:
                raise RuntimeError(f"{mod_name} has no main() entry point")

            if inspect.iscoroutinefunction(main_fn):
                await main_fn()
            else:
                # Run sync main() in a worker thread so we don't block event loop
                await asyncio.to_thread(main_fn)
    except SystemExit:
        # Some scripts call sys.exit() after main work
        pass
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:400]}"
    finally:
        try: stream.flush()
        except Exception: pass

    elapsed = time.time() - start

    # Give pump 2 more seconds to drain queue
    await asyncio.sleep(2.0)
    cancel_event.set()
    try: await asyncio.wait_for(pump_task, timeout=3.0)
    except Exception:
        pump_task.cancel()

    # Restore module
    try: _unpatch_module(mod, backup)
    except Exception: pass

    # Try to find any results JSON the script may have dumped
    json_payload = _find_results_json(mod_name)

    # Build TXT report
    txt = _build_txt_report(
        info=info, mod_name=mod_name, elapsed=elapsed,
        n_proxies=len(proxies), n_numbers=len(numbers) if numbers else 0,
        concurrency=concurrency, hits=hits, transcript=transcript,
        error_msg=error_msg, json_payload=json_payload,
    )

    # Send summary
    try:
        summary_lines = [
            f"<b>Test Complete: {info['label']}</b>",
            f"Time: {elapsed:.1f}s ({elapsed/60:.1f}min)",
            f"Hits: <b>{len(hits)}</b>",
            f"Transcript lines: {len(transcript)}",
        ]
        if error_msg:
            summary_lines.append(f"⚠️ Error: <code>{_truncate(error_msg, 180)}</code>")
        if json_payload:
            summary_lines.append(f"JSON dump: {len(json_payload)} keys")
        await context.bot.send_message(
            chat_id, "\n".join(summary_lines), parse_mode="HTML",
        )
    except Exception: pass

    # Send TXT file
    try:
        buf = io.BytesIO(txt.encode("utf-8"))
        buf.name = f"test_{short_name}_{int(time.time())}.txt"
        await context.bot.send_document(
            chat_id, document=buf,
            caption=f"📄 {info['label']} — {len(hits)} hits, {elapsed:.0f}s",
        )
    except Exception as e:
        try: await context.bot.send_message(chat_id, f"Couldn't send TXT: {str(e)[:200]}")
        except Exception: pass

    if on_done:
        try: on_done(short_name, hits, elapsed)
        except Exception: pass

    return {
        "ok": True, "mode": short_name, "hits": len(hits),
        "elapsed": elapsed, "error": error_msg,
        "transcript_lines": len(transcript),
    }


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _truncate(s: str, n: int) -> str:
    s = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", s)
    return s if len(s) <= n else s[:n - 3] + "..."


def _find_results_json(mod_name: str) -> Optional[Dict]:
    """Scripts dump their findings to /home/ubuntu/<mod>_results.json.
    Read it if present."""
    candidates = [
        f"/home/ubuntu/{mod_name}_results.json",
        f"/home/ubuntu/{mod_name.replace('_bruteforce','')}_results.json",
        f"/home/ubuntu/{mod_name.replace('_test','')}_results.json",
    ]
    for path in candidates:
        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception:
            continue
    return None


def _build_txt_report(*, info, mod_name, elapsed, n_proxies, n_numbers,
                       concurrency, hits, transcript, error_msg,
                       json_payload) -> str:
    """Build a detailed plain-text report."""
    lines: List[str] = []
    lines.append(f"# {info['label']}")
    lines.append(f"# Module: {mod_name}.py")
    lines.append(f"# Description: {info['desc']}")
    lines.append(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"# Runtime: {elapsed:.2f}s ({elapsed/60:.2f}min)")
    lines.append(f"# Bot proxies used: {n_proxies}")
    lines.append(f"# Bot numbers used: {n_numbers if n_numbers else '0 (script generated)'}")
    lines.append(f"# Concurrency cap: {concurrency}")
    if error_msg:
        lines.append(f"# Error: {error_msg}")
    lines.append("=" * 78)
    lines.append("")

    # Hits section
    lines.append(f"## SUCCESSFUL HITS ({len(hits)})")
    lines.append("-" * 78)
    if hits:
        for i, h in enumerate(hits, 1):
            lines.append(f"[{i:>4}] {h}")
    else:
        lines.append("(none)")
    lines.append("")

    # JSON dump if available
    if json_payload:
        lines.append("## SCRIPT RESULTS JSON")
        lines.append("-" * 78)
        try:
            lines.append(json.dumps(json_payload, indent=2, default=str)[:20000])
        except Exception:
            lines.append("(could not serialize)")
        lines.append("")

    # Full transcript at the end (last 3000 lines to keep under Telegram's 50MB)
    lines.append(f"## FULL STDOUT TRANSCRIPT (last 3000 lines, total {len(transcript)})")
    lines.append("-" * 78)
    tail = transcript[-3000:] if len(transcript) > 3000 else transcript
    lines.extend(tail)

    return "\n".join(lines)


def list_modes_lines() -> List[str]:
    """Return formatted lines describing each registered mode (for /help)."""
    out: List[str] = []
    for short, info in TEST_SCRIPTS.items():
        out.append(f"  /test {short:<10} — {info['label']}")
    return out
