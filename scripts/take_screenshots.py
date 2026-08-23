"""Capture documentation screenshots of the running app (dev convenience).

Usage: python scripts/take_screenshots.py http://127.0.0.1:5173
Requires: pip install playwright && playwright install chromium
"""

import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5173"
OUT = "docs/screenshots"

SHOTS = [
    ("dashboard", "#/", True),
    ("component-postgresql", "#/c/db-postgresql", True),
    ("impact-postgresql", "#/c/db-postgresql/impact", True),
    ("path-portal-postgresql", "#/path?from=svc-customer-portal&to=db-postgresql", True),
    ("impact-empty-portal", "#/c/svc-customer-portal/impact", False),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    for name, route, full in SHOTS:
        page.goto(f"{BASE}/{route}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(900)
        page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
        print(f"saved {OUT}/{name}.png")
    browser.close()
