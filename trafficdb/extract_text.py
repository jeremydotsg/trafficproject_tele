from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import codecs
import re
import time

def get_rate():
    # Initialize the Chrome driver with the specified options
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional but recommended)
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    #chrome_options.add_argument("--window-size=1920x1080")  # Set window size (optional)
    
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
