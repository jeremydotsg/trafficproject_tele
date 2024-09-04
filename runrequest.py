from requests_html import AsyncHTMLSession
from requests_html import HTML
from websockets import client
import asyncio

class CustomAsyncHTMLSession(AsyncHTMLSession):
    def __init__(self, chrome_path):
        super().__init__()
        self.chrome_path = chrome_path

    async def _browser(self):
        from pyppeteer.launcher import launch
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--incognito',
                '--no-sandbox',
                '--no-zygote',
                '--disable-software-rasterizer'
            ],
            #'executablePath': self.chrome_path
        })
        return browser

# Usage
async def main():
    session = CustomAsyncHTMLSession('/usr/bin/chromium-browser')
    browser = await session._browser()
    page = await browser.newPage()
    await page.goto('https://example.com')
    content = await page.content()
    print(content)
    await browser.close()

# Ensure there's an event loop running
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
