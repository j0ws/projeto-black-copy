from playwright.sync_api import sync_playwright
import os

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video", viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("Navigating to local HTML file...")
        # Get absolute path for frontend_prototype.html
        html_path = os.path.abspath("frontend_prototype.html")
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(1000)

        # 1. Test platform toggle and search
        print("Testing platform toggle and search...")
        # Since we are loading via file://, the fetch API will fail because of CORS/scheme if the backend is not running.
        # But we DO have the backend running. Wait, do we? Let's verify we spin up the backend inside the python script.
        import subprocess
        print("Starting backend...")
        backend_process = subprocess.Popen(["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd="/app/backend")
        page.wait_for_timeout(2000) # wait for backend to start

        page.locator("label:has-text('TikTok (Mock)')").click()
        page.wait_for_timeout(500)

        page.locator("#searchInput").fill("suco verde")
        page.wait_for_timeout(500)

        page.locator("#btnSearch").click()

        # Wait until the results container is visible
        page.locator("#resultsSection").wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1500) # Wait for backend mock to render

        # 2. Test Thumbnail Hover Debounce
        print("Testing thumbnail hover (debounce)...")
        first_thumb = page.locator(".aspect-video").first
        # Move mouse in and out quickly to test debounce
        first_thumb.hover()
        page.wait_for_timeout(100)
        page.mouse.move(0, 0) # move away
        page.wait_for_timeout(500) # wait for debounce to cancel

        # Now hover and wait to trigger iframe
        first_thumb.hover()
        page.wait_for_timeout(1500) # wait for iframe to inject
        page.mouse.move(0, 0) # move away
        page.wait_for_timeout(500) # wait for cleanup

        # 3. Test Dual Sliders Constraints
        print("Testing dual sliders constraint (max 20s)...")
        # Find the first start slider and try to drag it far apart
        start_slider = page.locator("input[type='range'][id^='slider-start']").first
        end_slider = page.locator("input[type='range'][id^='slider-end']").first

        start_slider.fill("0")
        page.wait_for_timeout(500)
        # Try to set end slider to 30 (should be blocked and adjust start or cap)
        # Actually range input fill fires change event, we trigger input manually
        page.evaluate("() => { const end = document.querySelector('input[id^=\"slider-end\"]'); end.value = 30; end.dispatchEvent(new Event('input')); }")
        page.wait_for_timeout(1000)

        # 4. Test Checkbox State Management
        print("Testing selection state management...")
        checkbox = page.locator("input[type='checkbox']").first
        checkbox.check()
        page.wait_for_timeout(1000)

        download_btn = page.locator("#btnDownloadSelected")
        print(f"Download button disabled state: {download_btn.is_disabled()}")

        page.screenshot(path="/home/jules/verification/verification.png", full_page=True)
        print("Verification complete.")

        context.close()
        browser.close()

if __name__ == "__main__":
    verify_frontend()
