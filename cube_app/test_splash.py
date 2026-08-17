from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto('http://localhost:5174/#/splash')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(500)
    page.screenshot(path='e:/BH/PyStudy/ICube/cube_app/splash_preview.png')
    print('Screenshot saved')
    browser.close()
