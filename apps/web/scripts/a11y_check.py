"""Accessibility scan: runs axe-core (WCAG 2.2 A/AA rules) on key pages. Fails on serious or critical issues.

usage: python scripts/a11y_check.py http://localhost:3000
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:3000"
PAGES = ["/", "/explore", "/start", "/results", "/ask", "/briefing", "/companies", "/roadmap", "/signin", "/report",
         "/participate", "/privacy", "/accessibility", "/about/data"] + sys.argv[2:]
axe = (Path(__file__).resolve().parent.parent / "node_modules/axe-core/axe.min.js").read_text()
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for reduced in (True, False):
        ctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce" if reduced else "no-preference")
        for path in PAGES:
            pg = ctx.new_page(); pg.goto(base + path); pg.wait_for_timeout(1500)
            pg.evaluate(axe)
            res = pg.evaluate("axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
            v = [x for x in res["violations"] if x["impact"] in ("serious", "critical")]
            tag = "reduced-motion" if reduced else "full"
            print(("FAIL" if v else "ok  "), tag, path)
            for x in v:
                bad += 1
                print("   ", x["impact"], x["id"], "-", x["help"], f"({len(x['nodes'])} nodes)", x["nodes"][0]["target"])
            pg.close()
    b.close()
sys.exit(1 if bad else 0)
