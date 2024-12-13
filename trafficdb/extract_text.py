import requests
import re

def get_rate():
    print("Start get rate.")
    # URL of the API endpoint
    api_url = "https://r.jina.ai/https://www.cimbclicks.com.sg/sgd-to-myr"
    headers = {"Content-Type": "application/json",
    "X-Locale": "en-US",
    "X-Retain-Images": "none",
    "X-No-Cache": "true",
    "X-With-Iframe": "true",
    "X-With-Shadow-Dom": "true"}
    
    # Regular expression to find the exchange rate
    pattern = r"MYR (\d+\.\d+)"
    
    # Send a GET request to the API
    response = requests.get(api_url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response text
        data = response.text
        
        # Print the retrieved data
        print(data)
        
        # Search for the pattern in the content
        match = re.search(pattern, data)
        
        if match:
            exchange_rate = match.group(1)
            print(f"Extracted Exchange Rate: {exchange_rate}")
            
            return f"{exchange_rate}"
        else:
            print("Exchange rate not found.")
            return data    
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        
    return f"Failed to retrieve data. Status code: {response.status_code}"
