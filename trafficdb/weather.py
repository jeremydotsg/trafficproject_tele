import requests
import json
from datetime import datetime
import time
import os
import logging
from dotenv import load_dotenv
import pytz
from collections import defaultdict

load_dotenv()
logger = logging.getLogger('trafficdb')

last_api_call_time = None
last_api_call_result = None

def call_my_api():
    headers = {'accept': 'application/json'}
    
    # Get the URL from environment variable
    url = os.getenv('MY_WEATHER_API_URL')

    # Make the request
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            my_weather_json = response.json()
            #print(json.dumps(data, indent=4))
            my_weather_json = convert_to_eng(my_weather_json)
            logger.info("Weather API: Called MY API.")
            return my_weather_json
        else:
            logger.info("Weather API: Called MY API and failed response. {}".format(response))
    except Exception as e:
        logger.error("Weather API: MY API Failed {}".format(e))
        
    return None

def call_sg_api():
    headers = {'accept': 'application/json'}
    
    # Get the URL from environment variable
    url = os.getenv('SG_WEATHER_API_URL')
    # Make the request
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sg_weather_json = response.json()
            logger.info("Weather API: Called SG API.")
            return sg_weather_json
        else:
            logger.info("Weather API: Called My API and failed response. {}".format(response))
    except Exception as e:
        logger.error("Weather API: SG API Failed {}".format(e))
    return None

def get_weather():
    global last_api_call_time
    global last_api_call_result
    if last_api_call_time is None or (datetime.now() - last_api_call_time).total_seconds() >= 3600:
        my_weather_json = call_my_api()
        sg_weather_json = call_sg_api()
        my_weather = parse_my_weather(my_weather_json, True)
        sg_weather = parse_sg_weather(sg_weather_json)
        last_api_call_result = sg_weather + my_weather
        last_api_call_time = datetime.now()
        return sg_weather + my_weather
    else:
        return last_api_call_result
    return "Not Available."
        
def convert_to_eng(my_weather_json):
    if my_weather_json:
        eng_json = None
        my_eng_dict = {
            "Berjerebu" : "Hazy",
            "Tiada hujan" : "No rain",
            "Hujan" : "Rain",
            "Hujan di beberapa tempat" : "Scattered rain",
            "Hujan di satu dua tempat" : "Isolated Rain",
            "Hujan di satu dua tempat di kawasan pantai" : "Isolated rain over coastal areas",
            "Hujan di satu dua tempat di kawasan pedalaman" : "Isolated rain over inland areas",
            "Ribut petir" : "Thunderstorms",
            "Ribut petir di beberapa tempat" : "Scattered thunderstorms",
            "Ribut petir di beberapa tempat di kawasan pedalaman" : "Scattered thunderstorms over inland areas",
            "Ribut petir di satu dua tempat" : "Isolated thunderstorms",
            "Ribut petir di satu dua tempat di kawasan pantai" : "Isolated thunderstorms over coastal areas",
            "Ribut petir di satu dua tempat di kawasan pedalaman" : "Isolated thunderstorms over inland areas",
            "Pagi" : "Morning",
            "Malam" : "Night",
            "Petang" : "Afternoon",
            "Pagi dan Petang" : "Morning and Afternoon",
            "Pagi dan Malam" : "Morning and Night",
            "Petang dan Malam" : "Afternoon and Night",
            "Sepanjang Hari" : "Throughout the Day"
            }
        
        for entry in my_weather_json:
            entry["morning_forecast"] = my_eng_dict.get(entry["morning_forecast"], entry["morning_forecast"])
            entry["afternoon_forecast"] = my_eng_dict.get(entry["afternoon_forecast"], entry["afternoon_forecast"])
            entry["night_forecast"] = my_eng_dict.get(entry["night_forecast"], entry["night_forecast"])
            entry["summary_forecast"] = my_eng_dict.get(entry["summary_forecast"], entry["summary_forecast"])
            entry["summary_when"] = my_eng_dict.get(entry["summary_when"], entry["summary_when"])
    return my_weather_json

def parse_my_weather(my_weather_json, today_only):
    if not my_weather_json:
        return "MY Weather Data Not Available."

    singapore_tz = pytz.timezone('Asia/Singapore')
    today_date = datetime.now(singapore_tz).strftime("%Y-%m-%d")
    my_json = [entry for entry in my_weather_json if not today_only or entry["date"] == today_date]

    display_string = ""
    for entry in my_json:
        display_string += f"<b><u>Johor Bahru Weather forecast ({entry['date']})</u></b>\n"
        display_string += f"Outlook: {entry['summary_forecast']} in the {entry['summary_when']}.\n\n"
        display_string += f"Morning: {entry['morning_forecast']}.\n"
        display_string += f"Afternoon: {entry['afternoon_forecast']}.\n"
        display_string += f"Night: {entry['night_forecast']}.\n"
    
    return display_string


def parse_sg_weather(sg_weather_data):
    if not sg_weather_data:
        return "SG Weather Data Not Available."

    else:
        record = sg_weather_data['data']['records'][0]
        general = record['general']
        periods = record['periods']
        
        forecast_emojis = {
            "Fair": "☀️",
            "Fair (Day)": "🌞",
            "Fair (Night)": "🌜",
            "Fair and Warm": "🌡️",
            "Partly Cloudy": "🌤️",
            "Partly Cloudy (Day)": "⛅",
            "Partly Cloudy (Night)": "☁️🌙",
            "Cloudy": "☁️",
            "Hazy": "🌫️",
            "Slightly Hazy": "🌁",
            "Windy": "🌬️",
            "Mist": "🌁",
            "Fog": "🌫️",
            "Light Rain": "🌦️",
            "Moderate Rain": "🌧️",
            "Heavy Rain": "🌧️🌧️",
            "Passing Showers": "🌦️",
            "Light Showers": "🌦️",
            "Showers": "🌧️",
            "Heavy Showers": "🌧️🌧️",
            "Thundery Showers": "⛈️",
            "Heavy Thundery Showers": "⛈️⛈️",
            "Heavy Thundery Showers with Gusty Winds": "⛈️🌬️"
        }
        # Display Summary
        weather_str = ""
        
        weather_str += f"<b><u>Singapore Weather Forecast for {general['validPeriod']['text']}.</u></b>\n"
        weather_str +=f"Outlook: {forecast_emojis.get(general['forecast']['text'], general['forecast']['text'])}"
        weather_str +=f"\n🌡️: {general['temperature']['low']} - {general['temperature']['high']} {general['temperature']['unit']}. "
        weather_str +=f"\n💧: {general['relativeHumidity']['low']}% - {general['relativeHumidity']['high']}% "
        weather_str +=f"\n🌬️: {general['wind']['speed']['low']} - {general['wind']['speed']['high']} km/h ({general['wind']['direction']})\n"
           
        # Display periods
        for period in periods:
            weather_str += f"\n{period['timePeriod']['text']}\n"
            forecast_groups = defaultdict(list)
            for region, forecast in period['regions'].items():
                forecast_groups[forecast['text']].append(region.capitalize())
            
            for forecast_text, regions in forecast_groups.items():
                if len(regions) == 5:  # All regions
                    weather_str += f"   All regions: {forecast_emojis.get(forecast_text,forecast_text)}\n"
                else:
                    regions_str = ', '.join(regions)
                    weather_str += f"   {regions_str}: {forecast_emojis.get(forecast_text,forecast_text)}\n"
        
        
        weather_str += "\n"
    
    return weather_str




    
