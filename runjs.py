from selenium import webdriver

# Initialize the PhantomJS WebDriver
driver = webdriver.PhantomJS()
# driver.set_window_size(1120, 550)

# Navigate to a web page
driver.get('https://www.google.com')

# Get the page title
print("Page title:", driver.title)

# Take a screenshot of the page
driver.save_screenshot('screenshot.png')

# Close the WebDriver
driver.quit()