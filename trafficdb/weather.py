import requests
import json
from datetime import datetime
import time
import os
import logging
from dotenv import load_dotenv
import pytz

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
    if last_api_call_time is None or (datetime.datetime.now() - last_api_call_time).total_seconds() >= 3600:
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
            "Berjerebu" : "Hazy.",
            "Tiada hujan" : "No rain.",
            "Hujan" : "Rain.",
            "Hujan di beberapa tempat" : "Scattered rain.",
            "Hujan di satu dua tempat" : "Isolated Rain.",
            "Hujan di satu dua tempat di kawasan pantai" : "Isolated rain over coastal areas.",
            "Hujan di satu dua tempat di kawasan pedalaman" : "Isolated rain over inland areas.",
            "Ribut petir" : "Thunderstorms.",
            "Ribut petir di beberapa tempat" : "Scattered thunderstorms.",
            "Ribut petir di beberapa tempat di kawasan pedalaman" : "Scattered thunderstorms over inland areas.",
            "Ribut petir di satu dua tempat" : "Isolated thunderstorms.",
            "Ribut petir di satu dua tempat di kawasan pantai" : "Isolated thunderstorms over coastal areas.",
            "Ribut petir di satu dua tempat di kawasan pedalaman" : "Isolated thunderstorms over inland areas.",
            "Pagi" : "Morning.",
            "Malam" : "Night.",
            "Petang" : "Afternoon.",
            "Pagi dan Petang" : "Morning and Afternoon.",
            "Pagi dan Malam" : "Morning and Night.",
            "Petang dan Malam" : "Afternoon and Night.",
            "Sepanjang Hari" : "Throughout the Day."
            }
        
        for entry in my_weather_json:
            entry["morning_forecast"] = my_eng_dict.get(entry["morning_forecast"], entry["morning_forecast"])
            entry["afternoon_forecast"] = my_eng_dict.get(entry["afternoon_forecast"], entry["afternoon_forecast"])
            entry["night_forecast"] = my_eng_dict.get(entry["night_forecast"], entry["night_forecast"])
            entry["summary_forecast"] = my_eng_dict.get(entry["summary_forecast"], entry["summary_forecast"])
            entry["summary_when"] = my_eng_dict.get(entry["summary_when"], entry["summary_when"])
    return my_weather_json

def parse_my_weather(my_weather_json, today_only):
    display_string = ""
    if my_weather_json:
        singapore_tz = pytz.timezone('Asia/Singapore')
        today_date = datetime.now(singapore_tz).strftime("%Y-%m-%d")
        my_json = my_weather_json
        if today_only:
            my_json = [entry for entry in my_weather_json if entry["date"] == today_date]
        for entry in my_json:
            display_string += "<b><u>Johor Bahru Weather forecast (" + entry["date"] + ")</u></b>"
            display_string += "\nMorning | Afternoon | Night\n"
            display_string += entry["morning_forecast"] + " | " + entry["afternoon_forecast"] + " | " + entry["night_forecast"]
            display_string += "\nSummary: " + entry["summary_forecast"] + " When: " + entry["summary_when"] + "\n"
    else:
        display_string = "MY Weather Data Not Available."
    return display_string


def parse_sg_weather(weather_data):
    weather_str = ""
    if weather_data:
        # Print general information
        general_info = weather_data["data"]["records"][0]["general"]
        weather_str += f"<b><u>Singapore Weather Forecast ({general_info['validPeriod']['text']})</u></b>"
        weather_str += "\n<u>Temperature | Humidity | Forecast | Wind Speed (Direction)</u>"
        weather_str += f"\n{general_info['temperature']['low']}°C - {general_info['temperature']['high']}°C | "
        weather_str += f" {general_info['relativeHumidity']['low']}% - {general_info['relativeHumidity']['high']}% | "
        weather_str += f" {general_info['forecast']['text']} | "
        weather_str += f" {general_info['wind']['speed']['low']} - {general_info['wind']['speed']['high']} km/h "
        weather_str += f" ({general_info['wind']['direction']}) "
        weather_str += "\n\n"
    
        # Print periods information
        periods = weather_data["data"]["records"][0]["periods"]
        if periods:
            weather_str += "<u>North | South | Central | East | West</u>\n"
        for period in periods:
            time_period = period["timePeriod"]["text"]
            regions = period["regions"]
            weather_str += f"<u>{time_period}</u>\n<i>"
            weather_str += regions["north"]["text"] + " | " + regions["south"]["text"] + " | " + regions["central"]["text"] + " | " + regions["east"]["text"] + " | " + regions["west"]["text"]
            weather_str += "</i>\n\n"
        
    else:
        weather_str = "SG Weather Data Not Available."

    return weather_str

    
