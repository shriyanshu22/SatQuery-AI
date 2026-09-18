import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Intercept console logs
        page.on("console", lambda msg: print(f"CONSOLE [{msg.type}]: {msg.text}"))

        # Intercept network requests and responses
        page.on("request", lambda request: print(f"REQ [{request.method}] {request.url}"))
        page.on("response", lambda response: print(f"RES [{response.status}] {response.url}"))

        print("Navigating to http://localhost:5173")
        await page.goto("http://localhost:5173")
        
        # Wait for the page to load and network idle
        await page.wait_for_load_state("networkidle")
        
        # Give it a second to see if checkBackendStatus fails
        await asyncio.sleep(2)
        
        # Create a dummy image for upload
        import os
        with open("test_dummy.png", "wb") as f:
            f.write(b"fake image data")

        print("Uploading image...")
        try:
            # Locate the file input by type
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files("test_dummy.png")
            
            # Wait for upload to complete
            await asyncio.sleep(3)
            
            # Click the submit query button
            print("Clicking Submit Query...")
            # We'll just look for a button that has the text "Submit" or "Run" or similar
            # Or use a generic click on the form submit
            await page.get_by_role("button", name="Run Analysis").click()
            
            await asyncio.sleep(3)
        except Exception as e:
            print(f"Error during interaction: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
