from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time

def get_rate():
    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--incognito')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')


    # Initialize the Chrome driver with the specified options
    driver = webdriver.Chrome(options=chrome_options)

    val = "https://www.cimbclicks.com.sg/sgd-to-myr"
    driver.get(val)

    # Wait for five seconds
    time.sleep(5)

    # Get the page source after the element is present
    page_source = driver.page_source

    soup = BeautifulSoup(page_source, features="html.parser")
    rateStr = soup.find(attrs={"class": "rateStr"})

    # Use regular expression to extract the rate
    rate = re.search(r"SGD 1.00 = MYR ([\d.]+)", rateStr.text).group(1)

    driver.quit()

    return rate