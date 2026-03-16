from playwright.sync_api import sync_playwright
import os
import subprocess

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(record_video_dir="/home/jules/verification/video2", viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("Starting backend...")
        backend_process = subprocess.Popen(["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], cwd="/app/backend")
        page.wait_for_timeout(2000) # wait for backend to start

        print("Navigating to local HTML file...")
        html_path = os.path.abspath("frontend_prototype.html")
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(1000)

        # Test Channel Autocomplete
        print("Testing autocomplete...")
        # Type the text slowly to trigger the input events properly
        page.locator("#filterChannel").type("fit", delay=100)
        page.wait_for_timeout(1000)

        # Check if dropdown appeared
        dropdown = page.locator("#channelAutocomplete")
        print(f"Dropdown is visible: {dropdown.is_visible()}")

        # Click the suggestion
        li_locator = page.locator("#channelSuggestions li:has-text('Fitness Pro')")
        if li_locator.is_visible():
            li_locator.click()
            page.wait_for_timeout(500)
        else:
            print("Suggestion not visible, skipping click.")

        # Search using TikTok mock since youtube transcript fails without valid video ID in mocked data
        page.locator("label:has-text('TikTok (Mock)')").click()
        page.wait_for_timeout(500)

        page.locator("#searchInput").fill("testo")
        page.wait_for_timeout(500)

        page.locator("#btnSearch").click()

        # Wait until the results container is visible
        page.locator("#resultsSection").wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(1500) # Wait for backend mock to render

        # Test Slider limits ([MatchTime - 5s] to [MatchTime + 15s])
        print("Checking sliders positioning...")
        # Get value of start and end
        start_val = page.locator("input[type='range'][id^='slider-start']").first.input_value()
        end_val = page.locator("input[type='range'][id^='slider-end']").first.input_value()
        print(f"Start: {start_val}, End: {end_val}")

        page.screenshot(path="/home/jules/verification/verification2.png", full_page=True)
        print("Verification complete.")

        context.close()
        browser.close()

if __name__ == "__main__":
    verify_frontend()
