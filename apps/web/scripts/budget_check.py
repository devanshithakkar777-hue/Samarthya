"""Low-data check: transferred JavaScript for the plain (reduced-motion / save-data) path must stay small.

usage: python scripts/budget_check.py http://localhost:3000 [max_kb]
"""
import sys
from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:3000"
MAX_KB = float(sys.argv[2]) if len(sys.argv) > 2 else 250
PAGES = ["/", "/explore", "/start", "/results"]
fail = False
with sync_playwright() as p:
    b = p.chromium.launch()
    for path in PAGES:
        ctx = b.new_context(reduced_motion="reduce"); pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg); cdp.send("Network.enable")
        reqs, total, js = {}, 0, 0
        cdp.on("Network.responseReceived", lambda e: reqs.__setitem__(e["requestId"], e["response"]["mimeType"]))
        def fin(e):
            global total, js
            n = e["encodedDataLength"]; total += n
            if "javascript" in reqs.get(e["requestId"], ""): js += n
        cdp.on("Network.loadingFinished", fin)
        pg.goto(base + path, wait_until="networkidle"); pg.wait_for_timeout(1500)
        kb = js / 1024
        ok = kb <= MAX_KB
        fail |= not ok
        print(("ok  " if ok else "FAIL"), f"{path:10s} JS {kb:6.1f} KB, all {total/1024:6.1f} KB (budget JS {MAX_KB:.0f} KB)")
        ctx.close()
    b.close()
sys.exit(1 if fail else 0)
