from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#from webdriver_manager.chrome import ChromeDriverManager
#from selenium.webdriver.chrome.service import Service as ChromeService
import logging
logger = logging.getLogger('trafficdb')

def get_rate():
    try:
        logger.info("Extract Text :: Start")
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.headless = True
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        logger.info("Extract Text :: Initiated Driver")
        # Initialize the Chrome driver with the specified options
        driver = webdriver.Chrome(options=chrome_options)
        logger.info(driver)
        logger.info("Extract Text :: Send URL to Driver")
        val = "https://www.cimbclicks.com.sg/sgd-to-myr"
        driver.get(val)
        logger.info("Extract Text :: Sleep for 10s")
        # Wait for the "rateStr" element to contain the text "SGD"
        time.sleep(10)
        logger.info("Extract Text :: Return page source")
        # Get the page source after the element is present
        page_source = driver.page_source
        driver.quit()
        soup = BeautifulSoup(page_source, features="html.parser")
        rateStr = soup.find(attrs={"class": "rateStr"})
        
        # Use regular expression to extract the rate
        rate = re.search(r"SGD 1.00 = MYR ([\d.]+)", rateStr.text).group(1)
        
        logger.info("Extract Text :: End")
        return rate
    except Exception as e:
        logger.error(e)
        return f"Error fetching exchange rate: {str(e)}"
