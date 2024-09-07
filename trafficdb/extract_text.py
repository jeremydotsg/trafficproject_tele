import requests
import re

def get_rate():
    print("Start get rate.")
    # URL of the API endpoint
    api_url = "https://r.jina.ai/https://www.cimbclicks.com.sg/sgd-to-myr"
    
    # Regular expression to find the exchange rate
    pattern = r"SGD 1.00 = MYR (\d+\.\d+)"
    
    # Send a GET request to the API
    response = requests.get(api_url)
    
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
            return "Exchange rate not found."    
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")
        
    return f"Failed to retrieve data. Status code: {response.status_code}"
