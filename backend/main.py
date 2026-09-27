from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import time
import httpx
from datetime import datetime, timedelta
from google import genai
from google.genai import types


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="WeatherGPT SIH26068",
    description="AI-powered weather assistant for Smart India Hackathon 2026",
    version="2.1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# OPEN-METEO
# ============================================================

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

OPEN_METEO_GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)


# ============================================================
# DEFAULT LOCATION — DELHI
# ============================================================

DELHI_LATITUDE = 28.6139
DELHI_LONGITUDE = 77.2090


# ============================================================
# KNOWN INDIAN CITIES
# ============================================================

CITY_COORDINATES = {
    "delhi": {
        "name": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "new delhi": {
        "name": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "mumbai": {
        "name": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "bombay": {
        "name": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "kolkata": {
        "name": "Kolkata",
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    "calcutta": {
        "name": "Kolkata",
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    "chennai": {
        "name": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    "madras": {
        "name": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    "bengaluru": {
        "name": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    "bangalore": {
        "name": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    "hyderabad": {
        "name": "Hyderabad",
        "latitude": 17.3850,
        "longitude": 78.4867
    },
    "ahmedabad": {
        "name": "Ahmedabad",
        "latitude": 23.0225,
        "longitude": 72.5714
    },
    "pune": {
        "name": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567
    }
}


# ============================================================
# GEMMA / GEMINI
# ============================================================

GEMMA_MODEL = "gemma-4-26b-a4b-it"

gemini_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "WeatherGPT backend is running",
        "project": "SIH26068",
        "status": "online",
        "ai_model": GEMMA_MODEL
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "WeatherGPT",
        "problem_statement": "SIH26068",
        "ai_enabled": gemini_client is not None,
        "ai_model": GEMMA_MODEL
    }


# ============================================================
# WEATHER CACHE
# ============================================================

_weather_cache = {}

WEATHER_CACHE_SECONDS = 60


# ============================================================
# LOCATION RESOLUTION CACHE
# ============================================================

_location_cache = {}


# ============================================================
# RESOLVE LOCATION
# ============================================================

def resolve_location(location="Delhi"):
    """
    Convert a city/location name into latitude and longitude.

    Known Indian cities use predefined coordinates.
    Other locations are searched using Open-Meteo geocoding.
    """

    if not location:
        location = "Delhi"

    location_clean = str(location).strip()

    if not location_clean:
        location_clean = "Delhi"

    location_key = location_clean.lower()

    # --------------------------------------------------------
    # Check predefined cities
    # --------------------------------------------------------

    if location_key in CITY_COORDINATES:
        return CITY_COORDINATES[location_key]

    # --------------------------------------------------------
    # Check location cache
    # --------------------------------------------------------

    if location_key in _location_cache:
        return _location_cache[location_key]

    # --------------------------------------------------------
    # Open-Meteo geocoding
    # --------------------------------------------------------

    params = {
        "name": location_clean,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    response = httpx.get(
        OPEN_METEO_GEOCODING_URL,
        params=params,
        timeout=10.0
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        raise ValueError(
            f"I could not find weather coordinates for '{location_clean}'."
        )

    result = results[0]

    resolved = {
        "name": result.get(
            "name",
            location_clean
        ),
        "latitude": result.get("latitude"),
        "longitude": result.get("longitude"),
        "country": result.get("country"),
        "admin1": result.get("admin1")
    }

    _location_cache[location_key] = resolved

    return resolved


# ============================================================
# WEATHER DATA FOR A LOCATION
# ============================================================

def get_weather_data_for_location(location="Delhi"):
    """
    Fetch current weather and 7-day forecast for a location.
    Results are cached for 60 seconds per location.
    """

    resolved_location = resolve_location(location)

    latitude = resolved_location["latitude"]
    longitude = resolved_location["longitude"]

    location_name = resolved_location.get(
        "name",
        location
    )

    cache_key = (
        f"{location_name.lower()}_"
        f"{latitude}_"
        f"{longitude}"
    )

    current_time = time.time()

    # --------------------------------------------------------
    # Return cached data if available
    # --------------------------------------------------------

    if cache_key in _weather_cache:

        cached_item = _weather_cache[cache_key]

        if (
            current_time - cached_item["time"]
            < WEATHER_CACHE_SECONDS
        ):
            return cached_item["data"]

    # --------------------------------------------------------
    # Open-Meteo parameters
    # --------------------------------------------------------

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum"
        ),
        "timezone": "Asia/Kolkata",
        "forecast_days": 7
    }

    response = httpx.get(
        OPEN_METEO_URL,
        params=params,
        timeout=10.0
    )

    response.raise_for_status()

    data = response.json()

    # --------------------------------------------------------
    # Store in cache
    # --------------------------------------------------------

    _weather_cache[cache_key] = {
        "time": current_time,
        "data": data
    }

    return data


# ============================================================
# DEFAULT WEATHER DATA — DELHI
# ============================================================

def get_weather_data():
    return get_weather_data_for_location("Delhi")


# ============================================================
# OPEN-METEO ARCHIVE (HISTORICAL DATA)
# ============================================================

OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

_climate_cache = {}

CLIMATE_CACHE_SECONDS = 3600  # 1 hour — historical data doesn't change often


def get_climate_data_for_location(location="Delhi", days=30):
    """
    Fetch historical daily weather for the last `days` days.
    Archive API has a short reporting lag, so we end the range
    2 days before today to avoid missing/partial data.
    """

    resolved_location = resolve_location(location)

    latitude = resolved_location["latitude"]
    longitude = resolved_location["longitude"]

    location_name = resolved_location.get("name", location)

    cache_key = f"{location_name.lower()}_{days}"

    current_time = time.time()

    if cache_key in _climate_cache:
        cached_item = _climate_cache[cache_key]
        if current_time - cached_item["time"] < CLIMATE_CACHE_SECONDS:
            return cached_item["data"]

    end_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days + 2)).strftime("%Y-%m-%d")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "temperature_2m_mean,"
            "precipitation_sum"
        ),
        "timezone": "Asia/Kolkata"
    }

    response = httpx.get(OPEN_METEO_ARCHIVE_URL, params=params, timeout=15.0)
    response.raise_for_status()

    data = response.json()

    _climate_cache[cache_key] = {
        "time": current_time,
        "data": data
    }

    return data


# ============================================================
# WEATHER API
# ============================================================

@app.get("/api/weather")
def weather():

    try:

        data = get_weather_data()

        current = data.get(
            "current",
            {}
        )

        daily = data.get(
            "daily",
            {}
        )

        return {
            "success": True,
            "location": "Delhi",

            "current": {

                "temperature": current.get(
                    "temperature_2m"
                ),

                "humidity": current.get(
                    "relative_humidity_2m"
                ),

                "apparent_temperature": current.get(
                    "apparent_temperature"
                ),

                "precipitation": current.get(
                    "precipitation"
                ),

                "weather_code": current.get(
                    "weather_code"
                ),

                "wind_speed": current.get(
                    "wind_speed_10m"
                )
            },

            "forecast": {

                "dates": daily.get(
                    "time",
                    []
                ),

                "weather_code": daily.get(
                    "weather_code",
                    []
                ),

                "max_temperature": daily.get(
                    "temperature_2m_max",
                    []
                ),

                "min_temperature": daily.get(
                    "temperature_2m_min",
                    []
                ),

                "precipitation": daily.get(
                    "precipitation_sum",
                    []
                )
            }
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# CLIMATE API
# ============================================================

@app.get("/api/climate")
def climate(location: str = "Delhi", days: int = 30):

    try:
        resolved_location = resolve_location(location)
        data = get_climate_data_for_location(location, days=days)

        daily = data.get("daily", {})

        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        mean_temps = daily.get("temperature_2m_mean", [])
        rainfall = daily.get("precipitation_sum", [])

        return {
            "success": True,
            "location": resolved_location.get("name", location),
            "source": "Open-Meteo Archive",

            "period": {
                "start": dates[0] if dates else None,
                "end": dates[-1] if dates else None
            },

            "daily": {
                "dates": dates,
                "max_temperature": max_temps,
                "min_temperature": min_temps,
                "mean_temperature": mean_temps,
                "precipitation": rainfall
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "daily": {
                "dates": [],
                "max_temperature": [],
                "min_temperature": [],
                "mean_temperature": [],
                "precipitation": []
            }
        }


# ============================================================
# WEATHER ALERT ENGINE
# ============================================================

def generate_weather_alerts(
    weather_data,
    location="Delhi"
):

    current = weather_data.get(
        "current",
        {}
    )

    daily = weather_data.get(
        "daily",
        {}
    )

    alerts = []

    temperature = current.get(
        "temperature_2m",
        0
    )

    wind_speed = current.get(
        "wind_speed_10m",
        0
    )

    precipitation = current.get(
        "precipitation",
        0
    )

    dates = daily.get(
        "time",
        []
    )

    max_temperatures = daily.get(
        "temperature_2m_max",
        []
    )

    precipitation_forecast = daily.get(
        "precipitation_sum",
        []
    )

    # ========================================================
    # CURRENT HEAT ALERT
    # ========================================================

    if temperature >= 40:

        alerts.append({
            "level": "RED",
            "title": "Extreme Heat",
            "location": location,
            "time": "Current",

            "description": (
                f"Current temperature is {temperature}°C. "
                "Extreme heat conditions are being detected."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Avoid prolonged exposure to extreme heat.",
                "Stay hydrated.",
                "Prefer shaded or cool areas."
            ]
        })

    elif temperature >= 38:

        alerts.append({
            "level": "ORANGE",
            "title": "High Heat",
            "location": location,
            "time": "Current",

            "description": (
                f"Current temperature is {temperature}°C. "
                "High heat conditions are being detected."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Stay hydrated.",
                "Avoid prolonged outdoor activity.",
                "Take breaks in shaded areas."
            ]
        })

    elif temperature >= 35:

        alerts.append({
            "level": "YELLOW",
            "title": "Heat Advisory",
            "location": location,
            "time": "Current",

            "description": (
                f"Current temperature is {temperature}°C. "
                "Elevated heat conditions are being detected."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Drink enough water.",
                "Limit prolonged exposure to direct sunlight."
            ]
        })

    # ========================================================
    # CURRENT RAIN ALERT
    # ========================================================

    if precipitation >= 20:

        alerts.append({
            "level": "ORANGE",
            "title": "Heavy Rain",
            "location": location,
            "time": "Current",

            "description": (
                f"Current precipitation is {precipitation} mm. "
                "Heavy rainfall conditions are being detected."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Take care while travelling.",
                "Avoid waterlogged areas.",
                "Monitor updated weather conditions."
            ]
        })

    elif precipitation >= 5:

        alerts.append({
            "level": "YELLOW",
            "title": "Rain Alert",
            "location": location,
            "time": "Current",

            "description": (
                f"Current precipitation is {precipitation} mm."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Carry rain protection.",
                "Use caution while travelling."
            ]
        })

    # ========================================================
    # CURRENT WIND ALERT
    # ========================================================

    if wind_speed >= 60:

        alerts.append({
            "level": "RED",
            "title": "Very Strong Winds",
            "location": location,
            "time": "Current",

            "description": (
                f"Wind speed is {wind_speed} km/h. "
                "Very strong winds are being detected."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Avoid unnecessary outdoor exposure.",
                "Stay away from loose objects and structures."
            ]
        })

    elif wind_speed >= 40:

        alerts.append({
            "level": "ORANGE",
            "title": "Strong Winds",
            "location": location,
            "time": "Current",

            "description": (
                f"Wind speed is {wind_speed} km/h."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Use caution outdoors.",
                "Secure loose objects."
            ]
        })

    # ========================================================
    # FUTURE RAIN ALERTS
    # ========================================================

    for i in range(len(dates)):

        if i >= len(precipitation_forecast):
            continue

        rain = precipitation_forecast[i]

        if rain >= 40:

            alerts.append({
                "level": "ORANGE",
                "title": "Heavy Rain Forecast",
                "location": location,
                "time": dates[i],

                "description": (
                    f"{rain} mm of precipitation is forecast "
                    f"for {dates[i]}."
                ),

                "source": "Open-Meteo",

                "precautions": [
                    "Plan travel carefully.",
                    "Be alert for possible waterlogging.",
                    "Monitor updated forecasts."
                ]
            })

        elif rain >= 20:

            alerts.append({
                "level": "YELLOW",
                "title": "Rain Forecast",
                "location": location,
                "time": dates[i],

                "description": (
                    f"{rain} mm of precipitation is forecast "
                    f"for {dates[i]}."
                ),

                "source": "Open-Meteo",

                "precautions": [
                    "Carry rain protection.",
                    "Plan outdoor activities accordingly."
                ]
            })

    # ========================================================
    # FUTURE HEAT ALERTS
    # ========================================================

    for i in range(len(dates)):

        if i >= len(max_temperatures):
            continue

        max_temp = max_temperatures[i]

        if max_temp >= 40:

            alerts.append({
                "level": "RED",
                "title": "Extreme Heat Forecast",
                "location": location,
                "time": dates[i],

                "description": (
                    f"Maximum temperature of {max_temp}°C "
                    f"is forecast for {dates[i]}."
                ),

                "source": "Open-Meteo",

                "precautions": [
                    "Avoid prolonged outdoor exposure.",
                    "Stay hydrated.",
                    "Plan outdoor activities during cooler hours."
                ]
            })

        elif max_temp >= 38:

            alerts.append({
                "level": "ORANGE",
                "title": "High Heat Forecast",
                "location": location,
                "time": dates[i],

                "description": (
                    f"Maximum temperature of {max_temp}°C "
                    f"is forecast for {dates[i]}."
                ),

                "source": "Open-Meteo",

                "precautions": [
                    "Stay hydrated.",
                    "Avoid prolonged exposure to direct sunlight."
                ]
            })

    # ========================================================
    # NO ALERT
    # ========================================================

    if not alerts:

        alerts.append({
            "level": "GREEN",
            "title": "No Significant Weather Alert",
            "location": location,
            "time": "Current",

            "description": (
                "No significant weather conditions meeting "
                "the WeatherGPT alert thresholds were detected."
            ),

            "source": "Open-Meteo",

            "precautions": [
                "Continue monitoring weather updates."
            ]
        })

    return alerts


# ============================================================
# ALERTS API
# ============================================================

@app.get("/api/alerts")
def alerts():

    try:

        weather_data = get_weather_data()

        generated_alerts = generate_weather_alerts(
            weather_data,
            location="Delhi"
        )

        return {
            "success": True,
            "source": "Open-Meteo",
            "official_warning": False,

            "message": (
                "WeatherGPT alerts generated from Open-Meteo "
                "weather and forecast data."
            ),

            "alerts": generated_alerts
        }

    except Exception as e:

        return {
            "success": False,
            "source": "Open-Meteo",
            "alerts": [],
            "message": "Unable to generate weather alerts.",
            "error": str(e)
        }


# ============================================================
# WHAT-IF ENGINE
# ============================================================

def what_if_analysis(
    scenario,
    temperature_change=0,
    rainfall_change=0,
    wind_change=0,
    location="Delhi"
):

    effects = []

    scenario_lower = scenario.lower()

    if temperature_change > 3:

        effects.append(
            "Higher temperature may increase heat stress."
        )

        effects.append(
            "Outdoor activities may become less comfortable."
        )

    elif temperature_change < -3:

        effects.append(
            "Lower temperature may increase cold stress."
        )

    if rainfall_change > 10:

        effects.append(
            "Higher rainfall may increase waterlogging risk."
        )

        effects.append(
            "Travel conditions may become more difficult."
        )

    elif rainfall_change < -10:

        effects.append(
            "Lower rainfall may increase dry-condition risk."
        )

    if wind_change > 15:

        effects.append(
            "Stronger winds may affect outdoor activities."
        )

        effects.append(
            "Loose objects may become a safety concern."
        )

    if (
        "farmer" in scenario_lower
        or "farming" in scenario_lower
    ):

        effects.append(
            "Farmers should monitor rainfall and temperature "
            "before irrigation or field operations."
        )

    if "travel" in scenario_lower:

        effects.append(
            "Travellers should monitor weather conditions "
            "before starting their journey."
        )

    if not effects:

        effects.append(
            "Weather impact is expected to be relatively "
            "limited under this scenario."
        )

    return {
        "scenario": scenario,
        "location": location,

        "changes": {
            "temperature_change": temperature_change,
            "rainfall_change": rainfall_change,
            "wind_change": wind_change
        },

        "effects": effects
    }


# ============================================================
# IMPACT CHAIN
# ============================================================

def impact_chain_analysis(
    weather_data,
    location="Delhi"
):

    current = weather_data.get(
        "current",
        {}
    )

    temperature = current.get(
        "temperature_2m",
        0
    )

    humidity = current.get(
        "relative_humidity_2m",
        0
    )

    wind_speed = current.get(
        "wind_speed_10m",
        0
    )

    precipitation = current.get(
        "precipitation",
        0
    )

    chain = []

    if temperature >= 40:

        chain.append({
            "stage": "Weather",
            "event": "Very high temperature",
            "impact": "Heat stress risk increases."
        })

    elif temperature >= 35:

        chain.append({
            "stage": "Weather",
            "event": "High temperature",
            "impact": "Heat discomfort may increase."
        })

    else:

        chain.append({
            "stage": "Weather",
            "event": "Moderate temperature",
            "impact": "No major temperature-related concern."
        })

    if precipitation > 10:

        chain.append({
            "stage": "Rainfall",
            "event": "Heavy rainfall",
            "impact": (
                "Waterlogging and travel disruption may occur."
            )
        })

    elif precipitation > 0:

        chain.append({
            "stage": "Rainfall",
            "event": "Rain detected",
            "impact": (
                "Outdoor activities may be affected."
            )
        })

    if wind_speed >= 40:

        chain.append({
            "stage": "Wind",
            "event": "Strong winds",
            "impact": (
                "Outdoor safety concerns may increase."
            )
        })

    if humidity >= 80:

        chain.append({
            "stage": "Humidity",
            "event": "High humidity",
            "impact": (
                "Perceived heat may increase."
            )
        })

    return {
        "location": location,
        "chain": chain
    }


# ============================================================
# SECTOR ADVISORY ENGINE
# ============================================================

def generate_sector_advisory(weather_data, location="Delhi"):

    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    wind_speed = current.get("wind_speed_10m", 0)

    weather_codes = daily.get("weather_code", [])
    max_temps = daily.get("temperature_2m_max", [])
    rain_forecast = daily.get("precipitation_sum", [])

    upcoming_max_temp = max(max_temps[:3]) if max_temps else current.get("temperature_2m", 0)
    upcoming_rain = max(rain_forecast[:3]) if rain_forecast else current.get("precipitation", 0)
    has_fog = any(45 <= code <= 48 for code in weather_codes[:3])

    sectors = {}

    # --------------------------------------------------------
    # AGRICULTURE
    # --------------------------------------------------------

    if upcoming_max_temp >= 40:
        ag_level = "RED"
        ag_recs = [
            "Extreme heat may stress crops and livestock.",
            "Increase irrigation frequency where possible.",
            "Avoid midday field work."
        ]
    elif upcoming_max_temp >= 36 or upcoming_rain >= 40:
        ag_level = "ORANGE"
        ag_recs = [
            "Monitor soil moisture closely.",
            "Plan irrigation or drainage accordingly.",
            "Protect sensitive crops from stress."
        ]
    elif upcoming_rain >= 20:
        ag_level = "YELLOW"
        ag_recs = [
            "Moderate rainfall expected — check field drainage.",
            "Delay fertilizer application if heavy rain is expected."
        ]
    else:
        ag_level = "GREEN"
        ag_recs = [
            "Conditions are generally favorable for normal farm operations."
        ]

    sectors["agriculture"] = {
        "title": "Agriculture",
        "risk_level": ag_level,
        "summary": (
            f"Upcoming max temperature ~{upcoming_max_temp}°C, "
            f"rainfall up to {upcoming_rain}mm expected in the next 3 days."
        ),
        "recommendations": ag_recs
    }

    # --------------------------------------------------------
    # AVIATION
    # --------------------------------------------------------

    if wind_speed >= 50:
        av_level = "RED"
        av_recs = [
            "Strong winds may cause significant turbulence and delays.",
            "Check updated flight advisories before travel."
        ]
    elif has_fog:
        av_level = "ORANGE"
        av_recs = [
            "Reduced visibility due to fog may affect takeoff/landing schedules.",
            "Check updated flight advisories before travel."
        ]
    elif wind_speed >= 30:
        av_level = "YELLOW"
        av_recs = [
            "Moderate winds may cause minor delays.",
            "Monitor airline updates for schedule changes."
        ]
    else:
        av_level = "GREEN"
        av_recs = [
            "No significant weather impact expected on flight operations."
        ]

    sectors["aviation"] = {
        "title": "Aviation",
        "risk_level": av_level,
        "summary": (
            f"Wind speed {wind_speed} km/h"
            + (", fog conditions possible in the next 3 days." if has_fog else ".")
        ),
        "recommendations": av_recs
    }

    # --------------------------------------------------------
    # MARINE
    # --------------------------------------------------------

    if wind_speed >= 40:
        ma_level = "RED"
        ma_recs = [
            "High winds may cause dangerous sea conditions.",
            "Avoid marine/boating activity.",
            "Secure vessels and equipment."
        ]
    elif wind_speed >= 25:
        ma_level = "ORANGE"
        ma_recs = [
            "Choppy waters possible.",
            "Exercise caution during marine operations."
        ]
    elif upcoming_rain >= 20:
        ma_level = "YELLOW"
        ma_recs = [
            "Rain may reduce visibility at sea.",
            "Monitor weather updates before departure."
        ]
    else:
        ma_level = "GREEN"
        ma_recs = [
            "Sea conditions expected to remain calm."
        ]

    sectors["marine"] = {
        "title": "Marine",
        "risk_level": ma_level,
        "summary": f"Wind speed {wind_speed} km/h, rainfall up to {upcoming_rain}mm expected.",
        "recommendations": ma_recs
    }

    # --------------------------------------------------------
    # URBAN
    # --------------------------------------------------------

    if upcoming_rain >= 40:
        ub_level = "RED"
        ub_recs = [
            "High risk of urban waterlogging.",
            "Avoid low-lying and flood-prone areas.",
            "Allow extra travel time."
        ]
    elif upcoming_rain >= 20 or upcoming_max_temp >= 40:
        ub_level = "ORANGE"
        ub_recs = [
            "Possible localized flooding or heat stress in urban areas.",
            "Plan outdoor activities accordingly."
        ]
    elif upcoming_max_temp >= 36:
        ub_level = "YELLOW"
        ub_recs = [
            "Elevated temperatures may affect outdoor workers.",
            "Stay hydrated during outdoor activity."
        ]
    else:
        ub_level = "GREEN"
        ub_recs = [
            "No significant urban weather concerns."
        ]

    sectors["urban"] = {
        "title": "Urban",
        "risk_level": ub_level,
        "summary": f"Max temperature ~{upcoming_max_temp}°C, rainfall up to {upcoming_rain}mm expected.",
        "recommendations": ub_recs
    }

    return sectors


# ============================================================
# ADVISORY API
# ============================================================

@app.get("/api/advisory")
def advisory(location: str = "Delhi"):

    try:
        resolved_location = resolve_location(location)
        data = get_weather_data_for_location(location)
        location_name = resolved_location.get("name", location)

        sectors = generate_sector_advisory(data, location=location_name)

        return {
            "success": True,
            "location": location_name,
            "sectors": sectors
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sectors": {}
        }


# ============================================================
# AI TOOL 1 — CURRENT WEATHER
# ============================================================

def tool_current_weather(location="Delhi"):

    resolved_location = resolve_location(location)

    data = get_weather_data_for_location(location)

    current = data.get(
        "current",
        {}
    )

    return {
        "location": resolved_location.get(
            "name",
            location
        ),

        "source": "Open-Meteo",

        "temperature": current.get(
            "temperature_2m"
        ),

        "humidity": current.get(
            "relative_humidity_2m"
        ),

        "feels_like": current.get(
            "apparent_temperature"
        ),

        "precipitation": current.get(
            "precipitation"
        ),

        "weather_code": current.get(
            "weather_code"
        ),

        "wind_speed": current.get(
            "wind_speed_10m"
        )
    }


# ============================================================
# AI TOOL 2 — FORECAST
# ============================================================

def tool_forecast(
    days_from_now=0,
    location="Delhi"
):

    resolved_location = resolve_location(location)

    data = get_weather_data_for_location(location)

    daily = data.get(
        "daily",
        {}
    )

    dates = daily.get(
        "time",
        []
    )

    max_temps = daily.get(
        "temperature_2m_max",
        []
    )

    min_temps = daily.get(
        "temperature_2m_min",
        []
    )

    rainfall = daily.get(
        "precipitation_sum",
        []
    )

    weather_codes = daily.get(
        "weather_code",
        []
    )

    try:

        index = int(days_from_now)

    except (ValueError, TypeError):

        index = 0

    if index < 0:
        index = 0

    if index >= len(dates):

        return {
            "success": False,

            "error": (
                "That date is outside the currently "
                "available 7-day forecast."
            ),

            "available_days": len(dates),

            "location": resolved_location.get(
                "name",
                location
            )
        }

    return {
        "success": True,

        "location": resolved_location.get(
            "name",
            location
        ),

        "source": "Open-Meteo",

        "days_from_now": index,

        "date": dates[index],

        "min_temperature": min_temps[index],

        "max_temperature": max_temps[index],

        "precipitation": rainfall[index],

        "weather_code": (
            weather_codes[index]
            if index < len(weather_codes)
            else None
        )
    }


# ============================================================
# AI TOOL 3 — FULL FORECAST
# ============================================================

def tool_full_forecast(location="Delhi"):

    resolved_location = resolve_location(location)

    data = get_weather_data_for_location(location)

    daily = data.get(
        "daily",
        {}
    )

    dates = daily.get(
        "time",
        []
    )

    max_temps = daily.get(
        "temperature_2m_max",
        []
    )

    min_temps = daily.get(
        "temperature_2m_min",
        []
    )

    rainfall = daily.get(
        "precipitation_sum",
        []
    )

    forecast = []

    for i in range(len(dates)):

        forecast.append({

            "date": dates[i],

            "min_temperature": (
                min_temps[i]
                if i < len(min_temps)
                else None
            ),

            "max_temperature": (
                max_temps[i]
                if i < len(max_temps)
                else None
            ),

            "precipitation": (
                rainfall[i]
                if i < len(rainfall)
                else None
            )
        })

    return {
        "success": True,

        "location": resolved_location.get(
            "name",
            location
        ),

        "source": "Open-Meteo",

        "forecast": forecast
    }


# ============================================================
# AI TOOL 4 — ALERTS
# ============================================================

def tool_weather_alerts(location="Delhi"):

    resolved_location = resolve_location(location)

    data = get_weather_data_for_location(location)

    location_name = resolved_location.get(
        "name",
        location
    )

    return {
        "success": True,

        "location": location_name,

        "source": "Open-Meteo",

        "official_warning": False,

        "alerts": generate_weather_alerts(
            data,
            location=location_name
        )
    }


# ============================================================
# AI TOOL 5 — IMPACT ANALYSIS
# ============================================================

def tool_weather_impact(location="Delhi"):

    resolved_location = resolve_location(location)

    data = get_weather_data_for_location(location)

    location_name = resolved_location.get(
        "name",
        location
    )

    return {
        "success": True,

        "location": location_name,

        "impact": impact_chain_analysis(
            data,
            location=location_name
        )
    }


# ============================================================
# AI TOOL 6 — WHAT IF
# ============================================================

def tool_what_if(
    scenario,
    temperature_change=0,
    rainfall_change=0,
    wind_change=0,
    location="Delhi"
):

    return what_if_analysis(
        scenario=scenario,

        temperature_change=temperature_change,

        rainfall_change=rainfall_change,

        wind_change=wind_change,

        location=location
    )


# ============================================================
# GEMMA TOOL DEFINITIONS
# ============================================================

weather_tool = types.Tool(
    function_declarations=[

        # ----------------------------------------------------
        # CURRENT WEATHER
        # ----------------------------------------------------

        {
            "name": "get_current_weather",

            "description": (
                "Get the current weather conditions "
                "for a location."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": (
                            "The city or location for which "
                            "weather information is required."
                        )
                    }
                },

                "required": [
                    "location"
                ]
            }
        },

        # ----------------------------------------------------
        # SPECIFIC DAY FORECAST
        # ----------------------------------------------------

        {
            "name": "get_forecast",

            "description": (
                "Get the weather forecast for a specific "
                "number of days from today."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": (
                            "The city or location."
                        )
                    },

                    "days_from_now": {

                        "type": "number",

                        "description": (
                            "Number of days from today. "
                            "0=today, 1=tomorrow, "
                            "2=day after tomorrow."
                        )
                    }
                },

                "required": [
                    "location",
                    "days_from_now"
                ]
            }
        },

        # ----------------------------------------------------
        # FULL FORECAST
        # ----------------------------------------------------

        {
            "name": "get_full_forecast",

            "description": (
                "Get the complete 7-day weather forecast "
                "for a location."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": (
                            "The city or location."
                        )
                    }
                },

                "required": [
                    "location"
                ]
            }
        },

        # ----------------------------------------------------
        # ALERTS
        # ----------------------------------------------------

        {
            "name": "get_weather_alerts",

            "description": (
                "Get WeatherGPT-generated weather alerts "
                "and potentially dangerous weather conditions."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": (
                            "The city or location."
                        )
                    }
                },

                "required": [
                    "location"
                ]
            }
        },

        # ----------------------------------------------------
        # IMPACT
        # ----------------------------------------------------

        {
            "name": "get_weather_impact",

            "description": (
                "Analyze how the current weather may affect "
                "people, travel, outdoor activities, farming, "
                "or other activities."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "location": {

                        "type": "string",

                        "description": (
                            "The city or location."
                        )
                    }
                },

                "required": [
                    "location"
                ]
            }
        },

        # ----------------------------------------------------
        # WHAT IF
        # ----------------------------------------------------

        {
            "name": "what_if_weather",

            "description": (
                "Analyze a hypothetical weather scenario "
                "and its potential effects."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "scenario": {

                        "type": "string",

                        "description": (
                            "The hypothetical weather scenario."
                        )
                    },

                    "temperature_change": {

                        "type": "number",

                        "description": (
                            "Temperature change in degrees Celsius."
                        )
                    },

                    "rainfall_change": {

                        "type": "number",

                        "description": (
                            "Rainfall change in millimeters."
                        )
                    },

                    "wind_change": {

                        "type": "number",

                        "description": (
                            "Wind speed change in km/h."
                        )
                    },

                    "location": {

                        "type": "string",

                        "description": (
                            "The city or location."
                        )
                    }
                },

                "required": [
                    "scenario"
                ]
            }
        }
    ]
)


# ============================================================
# GEMMA SYSTEM INSTRUCTION
# ============================================================

GEMMA_SYSTEM_INSTRUCTION = """

You are WeatherGPT, an intelligent conversational weather assistant.

Your job is to understand the user's actual question and conversation
context, not just match keywords.

You have access to real weather tools powered by Open-Meteo.

IMPORTANT RULES:

1. Never invent live weather data.

2. If the user asks about current weather, use
   get_current_weather.

3. If the user asks about a specific future day, use
   get_forecast.

4. If the user asks for a weekly, 7-day, or complete forecast,
   use get_full_forecast.

5. Interpret natural date expressions intelligently.

Examples:

"tomorrow" = 1 day from now

"day after tomorrow" = 2 days from now

"in three days" = 3 days from now

"three days from now" = 3 days from now

"after three days" = 3 days from now

"three days later" = 3 days from now

"in 3 days" = 3 days from now

"3 days from now" = 3 days from now

"next week" = approximately 7 days from now

6. If the user asks about alerts or warnings,
   use get_weather_alerts.

7. If the user asks how weather may affect activities,
   travel, outdoor plans, farming, events, or people,
   obtain the relevant weather data first and then explain
   the implications.

8. If the user asks a hypothetical "what if" question,
   use what_if_weather when appropriate.

9. You may combine information from multiple tools when
   necessary to answer a question.

10. Do not claim that WeatherGPT alerts are official government
    warnings. They are WeatherGPT-generated alerts based on
    Open-Meteo data.

11. Give clear, natural conversational answers.

12. If the user asks something unrelated to weather, politely
    explain that you are WeatherGPT and focus on weather-related
    assistance.

13. The default location is Delhi unless the user clearly
    specifies another location.

14. If a previous user message established a location and the
    current user message uses phrases such as:

    "tomorrow"
    "what about tomorrow?"
    "what about the next day?"
    "and the day after?"
    "will it rain?"
    "how about the weekend?"
    "will it be good for travelling?"

    preserve and use the previously established location.

15. If the user explicitly changes the location, use the new
    location instead of the previous location.

16. Always pass the correct location to the weather tool.

17. Do not expose internal tool names, API details, or
    implementation details to the user.

18. When explaining weather impacts, distinguish actual weather
    measurements from general advice.

19. Use the conversation history provided by the application to
    understand references such as "there", "tomorrow", "that city",
    "what about the weekend", and similar follow-up questions.

20. Do not assume that a previous weather answer is still current.
    When fresh weather information is needed, call the appropriate
    weather tool again.

Today's date is available from the application environment.

"""


# ============================================================
# CONVERSATION MEMORY
# ============================================================

# This is intentionally lightweight for the current prototype.
#
# The frontend does not need to change yet.
# Each session can optionally provide a "session_id".
#
# If no session_id is provided, "default" is used.
#
# Later, the frontend can generate a unique session_id for
# every user/conversation.

conversation_histories = {}

MAX_HISTORY_MESSAGES = 10

MAX_HISTORY_CHARACTERS = 6000


# ============================================================
# GET CONVERSATION HISTORY
# ============================================================

def get_conversation_history(
    session_id="default"
):

    if session_id not in conversation_histories:

        conversation_histories[session_id] = []

    return conversation_histories[session_id]


# ============================================================
# ADD TO CONVERSATION HISTORY
# ============================================================

def add_to_conversation_history(
    session_id,
    user_message,
    assistant_reply
):

    history = get_conversation_history(
        session_id
    )

    history.append({
        "role": "user",
        "content": user_message
    })

    history.append({
        "role": "assistant",
        "content": assistant_reply
    })

    # --------------------------------------------------------
    # Keep only recent messages
    # --------------------------------------------------------

    if len(history) > MAX_HISTORY_MESSAGES:

        del history[
            :-MAX_HISTORY_MESSAGES
        ]

    # --------------------------------------------------------
    # Keep total history reasonably small
    # --------------------------------------------------------

    while True:

        history_text = "\n".join(
            f"{item['role']}: {item['content']}"
            for item in history
        )

        if len(history_text) <= MAX_HISTORY_CHARACTERS:
            break

        if len(history) <= 2:
            break

        history.pop(0)


# ============================================================
# FORMAT CONVERSATION HISTORY
# ============================================================

def format_conversation_history(
    session_id="default"
):

    history = get_conversation_history(
        session_id
    )

    if not history:
        return "No previous conversation."

    lines = []

    for item in history:

        role = item.get(
            "role",
            "user"
        )

        content = item.get(
            "content",
            ""
        )

        lines.append(
            f"{role.upper()}: {content}"
        )

    return "\n".join(lines)


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_ai_tool(
    function_name,
    function_args
):

    if function_args is None:
        function_args = {}

    # --------------------------------------------------------
    # CURRENT WEATHER
    # --------------------------------------------------------

    if function_name == "get_current_weather":

        return tool_current_weather(
            location=function_args.get(
                "location",
                "Delhi"
            )
        )

    # --------------------------------------------------------
    # FORECAST
    # --------------------------------------------------------

    if function_name == "get_forecast":

        return tool_forecast(
            days_from_now=function_args.get(
                "days_from_now",
                0
            ),

            location=function_args.get(
                "location",
                "Delhi"
            )
        )

    # --------------------------------------------------------
    # FULL FORECAST
    # --------------------------------------------------------

    if function_name == "get_full_forecast":

        return tool_full_forecast(
            location=function_args.get(
                "location",
                "Delhi"
            )
        )

    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    if function_name == "get_weather_alerts":

        return tool_weather_alerts(
            location=function_args.get(
                "location",
                "Delhi"
            )
        )

    # --------------------------------------------------------
    # IMPACT
    # --------------------------------------------------------

    if function_name == "get_weather_impact":

        return tool_weather_impact(
            location=function_args.get(
                "location",
                "Delhi"
            )
        )

    # --------------------------------------------------------
    # WHAT IF
    # --------------------------------------------------------

    if function_name == "what_if_weather":

        return tool_what_if(

            scenario=function_args.get(
                "scenario",
                ""
            ),

            temperature_change=function_args.get(
                "temperature_change",
                0
            ),

            rainfall_change=function_args.get(
                "rainfall_change",
                0
            ),

            wind_change=function_args.get(
                "wind_change",
                0
            ),

            location=function_args.get(
                "location",
                "Delhi"
            )
        )

    return {
        "success": False,

        "error": (
            f"Unknown tool: {function_name}"
        )
    }


# ============================================================
# AI CHAT ENGINE
# ============================================================

def ask_gemma(
    user_message,
    session_id="default"
):

    if gemini_client is None:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    conversation_context = (
        format_conversation_history(
            session_id
        )
    )

    system_instruction = (

        GEMMA_SYSTEM_INSTRUCTION

        + f"\nToday's date is {today}."

        + "\n\nCURRENT CONVERSATION HISTORY:\n"

        + conversation_context

        + """



Use this conversation history only to understand context
and references.

If the current message refers to a previous location, preserve
that location unless the user clearly changes it.

Always obtain fresh weather data when answering a current or
forecast question.
"""
    )

    config = types.GenerateContentConfig(

        tools=[
            weather_tool
        ],

        system_instruction=system_instruction,

        temperature=0.2
    )

    # ========================================================
    # FIRST AI REQUEST
    # ========================================================

    response = gemini_client.models.generate_content(

        model=GEMMA_MODEL,

        contents=user_message,

        config=config
    )

    # ========================================================
    # TOOL LOOP
    # ========================================================

    max_tool_rounds = 5

    all_used_tools = []

    for _ in range(max_tool_rounds):

        function_calls = response.function_calls

        # ----------------------------------------------------
        # No tool required
        # ----------------------------------------------------

        if not function_calls:

            reply = response.text

            add_to_conversation_history(
                session_id,
                user_message,
                reply
            )

            return {
                "reply": reply,
                "tool_used": False,
                "tools": all_used_tools
            }

        tool_results = []

        # ----------------------------------------------------
        # Execute requested tools
        # ----------------------------------------------------

        for function_call in function_calls:

            function_name = function_call.name

            function_args = (
                function_call.args
                if function_call.args
                else {}
            )

            result = execute_ai_tool(
                function_name,
                function_args
            )

            all_used_tools.append(
                function_name
            )

            tool_results.append(

                types.Part.from_function_response(

                    name=function_name,

                    response={
                        "result": result
                    }
                )
            )

        # ----------------------------------------------------
        # Send tool results back to Gemma
        # ----------------------------------------------------

        response = gemini_client.models.generate_content(

            model=GEMMA_MODEL,

            contents=[
                user_message,
                response.candidates[0].content,
                *tool_results
            ],

            config=config
        )

        # ----------------------------------------------------
        # Final answer
        # ----------------------------------------------------

        if not response.function_calls:

            reply = response.text

            add_to_conversation_history(
                session_id,
                user_message,
                reply
            )

            return {
                "reply": reply,
                "tool_used": True,
                "tools": all_used_tools
            }

    # ========================================================
    # TOOL LOOP LIMIT
    # ========================================================

    fallback_reply = (
        "I was able to retrieve the weather information, "
        "but I could not finish processing the request."
    )

    add_to_conversation_history(
        session_id,
        user_message,
        fallback_reply
    )

    return {
        "reply": fallback_reply,
        "tool_used": True,
        "tools": all_used_tools
    }


# ============================================================
# CHAT API — AI POWERED + CONVERSATIONAL MEMORY
# ============================================================

@app.post("/api/chat")
def chat(request: dict):

    message = request.get(
        "message",
        ""
    ).strip()

    # --------------------------------------------------------
    # Optional session ID
    # --------------------------------------------------------

    session_id = request.get(
        "session_id",
        "default"
    )

    if not session_id:

        session_id = "default"

    # --------------------------------------------------------
    # Empty message
    # --------------------------------------------------------

    if not message:

        return {
            "success": False,

            "reply": (
                "Please ask me a weather question."
            ),

            "type": "general"
        }

    # ========================================================
    # AI CHAT
    # ========================================================

    try:

        result = ask_gemma(
            message,
            session_id=session_id
        )

        return {

            "success": True,

            "reply": result["reply"],

            "type": "ai",

            "data": {

                "ai_model": GEMMA_MODEL,

                "tool_used": result[
                    "tool_used"
                ],

                "tools": result[
                    "tools"
                ],

                "session_id": session_id
            }
        }

    except Exception as e:

        print(
            "AI CHAT ERROR:",
            str(e)
        )

        # ====================================================
        # SAFE FALLBACK
        # ====================================================

        try:

            weather_data = get_weather_data()

            current = weather_data.get(
                "current",
                {}
            )

            temperature = current.get(
                "temperature_2m"
            )

            humidity = current.get(
                "relative_humidity_2m"
            )

            apparent_temperature = current.get(
                "apparent_temperature"
            )

            wind_speed = current.get(
                "wind_speed_10m"
            )

            return {

                "success": True,

                "reply": (

                    "The AI assistant is temporarily unavailable. "

                    f"Current Delhi weather is {temperature}°C, "

                    f"feels like {apparent_temperature}°C, "

                    f"with {humidity}% humidity and "

                    f"wind speed of {wind_speed} km/h."
                ),

                "type": "weather_fallback",

                "data": {

                    "temperature": temperature,

                    "humidity": humidity,

                    "feels_like": apparent_temperature,

                    "wind_speed": wind_speed
                }
            }

        except Exception as fallback_error:

            return {

                "success": False,

                "reply": (
                    "I could not process the weather request "
                    "right now."
                ),

                "type": "error",

                "error": str(
                    fallback_error
                )
            }


# ============================================================
# CLEAR CHAT MEMORY
# ============================================================

@app.post("/api/chat/clear")
def clear_chat(request: dict):

    session_id = request.get(
        "session_id",
        "default"
    )

    if not session_id:

        session_id = "default"

    conversation_histories.pop(
        session_id,
        None
    )

    return {

        "success": True,

        "message": (
            "Conversation memory cleared."
        ),

        "session_id": session_id
    }


# ============================================================
# MULTI-CITY WEATHER
# ============================================================

CITIES = [

    {
        "name": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090
    },

    {
        "name": "Mumbai",
        "latitude": 19.0760,
        "longitude": 72.8777
    },

    {
        "name": "Kolkata",
        "latitude": 22.5726,
        "longitude": 88.3639
    },

    {
        "name": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707
    },

    {
        "name": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946
    },

    {
        "name": "Hyderabad",
        "latitude": 17.3850,
        "longitude": 78.4867
    },

    {
        "name": "Ahmedabad",
        "latitude": 23.0225,
        "longitude": 72.5714
    },

    {
        "name": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567
    }
]


# ============================================================
# MULTI-CITY WEATHER DATA
# ============================================================

def get_multi_city_weather_data():

    latitudes = ",".join(
        str(city["latitude"])
        for city in CITIES
    )

    longitudes = ",".join(
        str(city["longitude"])
        for city in CITIES
    )

    params = {

        "latitude": latitudes,

        "longitude": longitudes,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "wind_speed_10m"
        ),

        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum"
        ),

        "timezone": "Asia/Kolkata",

        "forecast_days": 7
    }

    response = httpx.get(

        OPEN_METEO_URL,

        params=params,

        timeout=10.0
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# MULTI-CITY WEATHER API
# ============================================================

@app.get("/api/weather/cities")
def weather_cities():

    try:

        raw_data = get_multi_city_weather_data()

        if isinstance(
            raw_data,
            dict
        ):

            raw_data = [
                raw_data
            ]

        cities_result = []

        for index, city in enumerate(CITIES):

            if index >= len(raw_data):
                continue

            city_data = raw_data[index]

            current = city_data.get(
                "current",
                {}
            )

            daily = city_data.get(
                "daily",
                {}
            )

            city_weather_data = {

                "current": current,

                "daily": daily
            }

            city_alerts = generate_weather_alerts(

                city_weather_data,

                location=city["name"]
            )

            cities_result.append({

                "name": city["name"],

                "latitude": city["latitude"],

                "longitude": city["longitude"],

                "current": {

                    "temperature": current.get(
                        "temperature_2m"
                    ),

                    "humidity": current.get(
                        "relative_humidity_2m"
                    ),

                    "apparent_temperature": current.get(
                        "apparent_temperature"
                    ),

                    "precipitation": current.get(
                        "precipitation"
                    ),

                    "wind_speed": current.get(
                        "wind_speed_10m"
                    )
                },

                "forecast": {

                    "dates": daily.get(
                        "time",
                        []
                    ),

                    "max_temperature": daily.get(
                        "temperature_2m_max",
                        []
                    ),

                    "min_temperature": daily.get(
                        "temperature_2m_min",
                        []
                    ),

                    "precipitation": daily.get(
                        "precipitation_sum",
                        []
                    )
                },

                "alerts": city_alerts
            })

        return {

            "success": True,

            "cities": cities_result
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e),

            "cities": []
        }