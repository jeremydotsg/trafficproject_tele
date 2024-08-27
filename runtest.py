from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re
import time
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

# Set up Firefox options for headless mode
firefox_options = Options()
firefox_options.headless = True
firefox_options.add_argument("--headless")

# Initialize the Firefox driver with the specified options
driver = webdriver.Firefox(options=firefox_options,service=FirefoxService(GeckoDriverManager().install()))

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

print(rate)
