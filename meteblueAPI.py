import requests
import logging
import configparser

# Configure logging
logging.basicConfig(filename='meteblue_api.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to get API key from config file
def get_api_key():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['Meteoblue']['API_KEY']


def api_pull(lat, lon, api_key):
    # API endpoint URL
    url = f'http://my.meteoblue.com/packages/basic-6h_basic-day_sunmoon?lat={lat}&lon={lon}&apikey={api_key}&windspeed=kmh'

    try:
        # Make GET request to the API
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        data = response.json()
        logging.info(f'Successfully pulled data for lat: {lat}, lon: {lon}')
        return data
    except requests.exceptions.HTTPError as http_err:
        logging.error(f'HTTP error occurred: {http_err} - Status Code: {response.status_code}')
        return None
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f'Connection error occurred: {conn_err}')
        return None
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f'Timeout error occurred: {timeout_err}')
        return None
    except requests.exceptions.RequestException as req_err:
        logging.error(f'An unexpected error occurred with the request: {req_err}')
        return None
    except Exception as e:
        logging.error(f'An unexpected error occurred: {e}')
        return None


def format_data(lat, lon):
    api_key_to_use = get_api_key()
    formatted_data = {}
    data = api_pull(lat, lon, api_key_to_use)
    if data is not None:
        # Overview
        overview = get_overview(data)
        formatted_data['overview'] = overview

        # Daily Summary
        day0_summary = get_daily_summary(data, 0)
        day1_summary = get_daily_summary(data, 1)
        day2_summary = get_daily_summary(data, 2)

        #Hour Summary
        day0_6 = get_hour_summary(data,1)
        day0_12 = get_hour_summary(data,2)
        day0_18 = get_hour_summary(data,3)
        day1_6 = get_hour_summary(data,5)
        day1_12 = get_hour_summary(data,6)
        day1_18 = get_hour_summary(data,7)

        sms_data = f"""
{overview}
- Today:{day0_summary}
- 6am: 
{day0_6}
- 12pm: 
{day0_12}
- 6pm: 
{day0_18}

- Tomorrow:{day1_summary}
- 6am: 
{day1_6}
- 12pm: 
{day1_12}
- 6pm: 
{day1_18}

- Following Day:{day2_summary}"""
    else:
        sms_data = "Cannot format data"
    
    return sms_data

def get_overview(data):
    update_time = data['metadata']['modelrun_updatetime_utc']
    latitude = data['metadata']['latitude']
    longitude = data['metadata']['longitude']
    
    overview = f"""
Last Updated: {update_time}
Lat: {latitude}
Lon: {longitude}
    """
    
    return overview

def get_daily_summary(data, day_index):
    day_time = data['data_day']['time'][day_index]
    day_temp_max = data['data_day']['temperature_max'][day_index]
    day_temp_min = data['data_day']['temperature_min'][day_index]
    day_rain = data['data_day']['precipitation'][day_index]
    day_wind = data['data_day']['windspeed_max'][day_index]
    day_sunrise = data['data_day']['sunrise'][day_index]
    day_sunset = data['data_day']['sunset'][day_index]
    day_pic = pictogram_day(data['data_day']['pictocode'][day_index])

    daily_summary = f""" {day_time}
{day_pic}
Temp Min: {day_temp_min:.0f} C
Temp Max: {day_temp_max:.0f} C
Rain: {day_rain} mm
Wind Gusts: {day_wind:.0f} kph
Sunrise: {day_sunrise}
Sunset: {day_sunset}
"""
    return daily_summary

def get_hour_summary(data, day_index):
    temp = data['data_6h']['temperature_instant'][day_index]
    rain = data['data_6h']['precipitation'][day_index]
    wind = data['data_6h']['windspeed_max'][day_index]

    hour_summary = f"""Temp: {temp:.0f} C
Rain: {rain} mm
Wind Gusts: {wind:.0f} kph"""
    return hour_summary 
    


def pictogram_day(num):
    weather_conditions = {
    1: "Sunny, cloudless sky",
    2: "Sunny and few clouds",
    3: "Partly cloudy",
    4: "Overcast",
    5: "Fog",
    6: "Overcast with rain",
    7: "Mixed with showers",
    8: "Showers, thunderstorms likely",
    9: "Overcast with snow",
    10: "Mixed with snow showers",
    11: "Mostly cloudy with a mixture of snow and rain",
    12: "Overcast with light rain",
    13: "Overcast with light snow",
    14: "Mostly cloudy with rain",
    15: "Mostly cloudy with snow",
    16: "Mostly cloudy with light rain",
    17: "Mostly cloudy with light snow",
    }

    return (weather_conditions[num])
    
    
