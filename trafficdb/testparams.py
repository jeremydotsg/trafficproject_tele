'''
Created on 23 Jul 2024

@author: Jeremy
'''
import re

def has_params(pattern, chat_text):
    match = re.match(pattern, chat_text)
    if match:
        command, param = match.groups()
        is_process = True
        if param:
            has_param = True
            print("Param: " + param)
        print("Command: " + command)

pattern = r"\/(\w+)\s?([\w\s]*)"

chat_text = "weather"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)

chat_text = "/weather"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)

chat_text = "/weather 1"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)
    
chat_text = "/weather 1 2"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)

chat_text = "/weather 1 2 3"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)
    
chat_text = "/weather ku ku ku"
print("Chat Text: " + chat_text)
has_params(pattern, chat_text)
match = re.findall(pattern, chat_text)
if match:
    print(match)
    

param_pattern = "^\d+(?: \d+)*$"
test_text = "12345"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1 2"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)
test_text = "1 a"
print(test_text)
match = re.findall(param_pattern, test_text)
if match:
    print(match)


import json

# Sample JSON response
json_response = {
    "code": 0,
    "data": {
        "records": [
            {
                "date": "2024-08-02",
                "updatedTimestamp": "2024-08-02T14:40:54+08:00",
                "general": {
                    "temperature": {
                        "low": 25,
                        "high": 34,
                        "unit": "Degrees Celsius"
                    },
                    "relativeHumidity": {
                        "low": 60,
                        "high": 95,
                        "unit": "Percentage"
                    },
                    "forecast": {
                        "code": "TL",
                        "text": "Thundery Showers"
                    },
                    "validPeriod": {
                        "start": "2024-08-02T12:00:00+08:00",
                        "end": "2024-08-03T12:00:00+08:00",
                        "text": "12 PM 2 Aug to 12 PM 3 Aug"
                    },
                    "wind": {
                        "speed": {
                            "low": 10,
                            "high": 20
                        },
                        "direction": "SSE"
                    }
                },
                "periods": [
                    {
                        "timePeriod": {
                            "start": "2024-08-02T12:00:00+08:00",
                            "end": "2024-08-02T18:00:00+08:00",
                            "text": "Midday to 6 pm 02 Aug"
                        },
                        "regions": {
                            "west": {
                                "code": "TL",
                                "text": "Thundery Showers"
                            },
                            "east": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            },
                            "central": {
                                "code": "TL",
                                "text": "Thundery Showers"
                            },
                            "south": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            },
                            "north": {
                                "code": "TL",
                                "text": "Thundery Showers"
                            }
                        }
                    },
                    {
                        "timePeriod": {
                            "start": "2024-08-02T18:00:00+08:00",
                            "end": "2024-08-03T06:00:00+08:00",
                            "text": "6 pm 02 Aug to 6 am 03 Aug"
                        },
                        "regions": {
                            "west": {
                                "code": "PN",
                                "text": "Partly Cloudy (Night)"
                            },
                            "east": {
                                "code": "PN",
                                "text": "Partly Cloudy (Night)"
                            },
                            "central": {
                                "code": "PN",
                                "text": "Partly Cloudy (Night)"
                            },
                            "south": {
                                "code": "PN",
                                "text": "Partly Cloudy (Night)"
                            },
                            "north": {
                                "code": "PN",
                                "text": "Partly Cloudy (Night)"
                            }
                        }
                    },
                    {
                        "timePeriod": {
                            "start": "2024-08-03T06:00:00+08:00",
                            "end": "2024-08-03T12:00:00+08:00",
                            "text": "6 am to Midday 03 Aug"
                        },
                        "regions": {
                            "west": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            },
                            "east": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            },
                            "central": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            },
                            "south": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            },
                            "north": {
                                "code": "PC",
                                "text": "Partly Cloudy (Day)"
                            }
                        }
                    }
                ],
                "timestamp": "2024-08-02T14:32:00+08:00"
            }
        ]
    },
    "errorMsg": ""
}

from collections import defaultdict

forecast_emojis = {
    "Thundery Showers": "⛈️",
    "Partly Cloudy (Day)": "⛅",
    "Partly Cloudy (Night)": "🌙"
}

# Function to parse and display weather data
def display_weather(data):
    record = data['data']['records'][0]
    general = record['general']
    periods = record['periods']
    
    # Display Summary
    weather_str = ""
    
    weather_str += f"Singapore Weather Forecast for {general['validPeriod']['text']}.\n"
    weather_str +=f"{general['forecast']['text']} with "
    weather_str +=f"temperature between {general['temperature']['low']} - {general['temperature']['high']} {general['temperature']['unit']}. "
    weather_str +=f"Relative humidity between {general['relativeHumidity']['low']}% - {general['relativeHumidity']['high']}% with "
    weather_str +=f"wind {general['wind']['speed']['low']} - {general['wind']['speed']['high']} km/h blowing from {general['wind']['direction']}.\n\n"
       
    # Display periods
    for period in periods:
        weather_str += f"\n{period['timePeriod']['text']}\n"
        forecast_groups = defaultdict(list)
        for region, forecast in period['regions'].items():
            forecast_groups[forecast['text']].append(region.capitalize())
        
        for forecast_text, regions in forecast_groups.items():
            if len(regions) == 5:  # All regions
                weather_str += f"   All regions: {forecast_text}\n"
            else:
                regions_str = ', '.join(regions)
                weather_str += f"   {regions_str}: {forecast_text}\n"

    print(weather_str)
# Display the weather data
display_weather(json_response)

    