"""Render docs/graph-model.svg to docs/graph-model.png for the README."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1200, "height": 720})
    page.goto("file:///home/user/dependency-detective/docs/graph-model.svg")
    page.wait_for_timeout(400)
    page.locator("svg").screenshot(path="docs/graph-model.png")
    b.close()
print("wrote docs/graph-model.png")
