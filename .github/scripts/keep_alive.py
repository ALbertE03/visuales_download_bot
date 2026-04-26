import os
import time
from playwright.sync_api import sync_playwright


def run():
    url = os.environ.get("STREAMLIT_URL")
    if not url:
        print("Error: STREAMLIT_URL environment variable is not set.")
        exit(1)

    print(f"Starting keep-alive ping for: {url}")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            print(f"Navigating to URL...")
            page.goto(url, wait_until="networkidle", timeout=60000)

            print("⏳ Waiting for application to stabilize...")
            time.sleep(15)

            title = page.title()
            print(f"Successfully reached: '{title}'")
            browser.close()
            print("Browser closed. App should be awake now.")

        except Exception as e:
            print(f"An error occurred: {e}")
            exit(1)


if __name__ == "__main__":
    run()
