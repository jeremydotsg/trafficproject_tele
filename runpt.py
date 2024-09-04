import asyncio
from pyppeteer import launch
from websockets import client

async def main():
    try:
        browser = await launch(
                headless=True,
                #executablePath="/usr/bin/chromium-browser",
                args=['--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--incognito',
                '--no-sandbox',
                '--no-zygote',
                '--disable-software-rasterizer']
            )
        page = await browser.newPage()
        await page.goto('https://www.cimbclicks.com.sg/sgd-to-myr')
    
        # Wait for the exchange rate element to load
        #await page.waitForSelector('#rateStr')  # Replace with the actual selector
    
        # Extract the exchange rate
        #exchange_rate = await page.evaluate('document.querySelector("#rateStr").textContent')  # Replace with the actual selector
        print(page)
    
        await browser.close()
    
    except Exception as e:
       print(f"Error: {e}")

asyncio.get_event_loop().run_until_complete(main())