from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

def get_rate():
    try:
        # Set up Firefox options for headless mode
        firefox_options = Options()
        firefox_options.headless = True
        firefox_options.add_argument("--headless")
        
        # Initialize the Firefox driver with the specified options
        driver = webdriver.Firefox(options=firefox_options, service=FirefoxService(GeckoDriverManager().install()))
        
        val = "https://www.cimbclicks.com.sg/sgd-to-myr"
        driver.get(val)
        
        # Wait for the "rateStr" element to contain the text "SGD"
        wait = WebDriverWait(driver, 10)
        element_locator = (By.CLASS_NAME, 'rateStr')
        wait.until(EC.text_to_be_present_in_element(element_locator, "SGD"))
        
        # Get the page source after the element is present
        page_source = driver.page_source
        
        soup = BeautifulSoup(page_source, features="html.parser")
        rateStr = soup.find(attrs={"class": "rateStr"})
        
        # Use regular expression to extract the rate
        rate = re.search(r"SGD 1.00 = MYR ([\d.]+)", rateStr.text).group(1)
        
        driver.quit()
        
        return rate
    except Exception as e:
        return f"Error fetching exchange rate: {str(e)}"
