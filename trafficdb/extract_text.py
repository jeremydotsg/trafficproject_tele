import requests
import re

def get_rate():
    """Retrieve and extract the exchange rate from a given API."""
    print("Start get rate.")
    
    api_url = "https://r.jina.ai/https://www.cimbclicks.com.sg/sgd-to-myr"
    headers = {
        "Content-Type": "application/json",
        "X-Locale": "en-US",
        "X-Retain-Images": "none",
        "X-No-Cache": "true",
        "X-With-Iframe": "true",
        "X-With-Shadow-Dom": "true"
    }
    
    pattern = r"MYR (\d+\.\d+)"
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.text
        print(data)
        
        match = re.search(pattern, data)
        
        if match:
            exchange_rate = match.group(1)
            print(f"Extracted Exchange Rate: {exchange_rate}")
            return exchange_rate
        else:
            print("Exchange rate not found.")
            return "Exchange rate not found."    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return f"Request failed: {e}."
    except re.error as e:
        print(f"Regex error: {e}")
        return f"Regex error: {e}"
