from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="WeatherGPT SIH26068",
    description="AI-powered weather assistant for Smart India Hackathon 2026",
    version="1.0.0"
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


# ============================================================
# DELHI LOCATION
# ============================================================

DELHI_LATITUDE = 28.6139
DELHI_LONGITUDE = 77.2090


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "WeatherGPT backend is running",
        "project": "SIH26068",
        "status": "online"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "WeatherGPT",
        "problem_statement": "SIH26068"
    }


# ============================================================
# WEATHER DATA
# ============================================================

def get_weather_data():

    params = {
        "latitude": DELHI_LATITUDE,
        "longitude": DELHI_LONGITUDE,

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

    return response.json()


# ============================================================
# WEATHER API
# ============================================================

@app.get("/api/weather")
def weather():

    try:

        data = get_weather_data()

        current = data.get("current", {})
        daily = data.get("daily", {})

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
# WEATHER ALERT ENGINE
# OPEN-METEO ONLY
# ============================================================

def generate_weather_alerts(weather_data):

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
            "location": "Delhi",
            "time": "Current",

            "description": (
                f"Current temperature is "
                f"{temperature}°C. Extreme heat "
                "conditions are being detected."
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
            "location": "Delhi",
            "time": "Current",

            "description": (
                f"Current temperature is "
                f"{temperature}°C. High heat "
                "conditions are being detected."
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
            "location": "Delhi",
            "time": "Current",

            "description": (
                f"Current temperature is "
                f"{temperature}°C. Elevated heat "
                "conditions are being detected."
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
            "location": "Delhi",
            "time": "Current",

            "description": (
                f"Current precipitation is "
                f"{precipitation} mm. Heavy rainfall "
                "conditions are being detected."
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
            "location": "Delhi",
            "time": "Current",

            "description": (
                f"Current precipitation is "
                f"{precipitation} mm."
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
            "location": "Delhi",
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
            "location": "Delhi",
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
                "location": "Delhi",
                "time": dates[i],

                "description": (
                    f"{rain} mm of precipitation is "
                    f"forecast for {dates[i]}."
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
                "location": "Delhi",
                "time": dates[i],

                "description": (
                    f"{rain} mm of precipitation is "
                    f"forecast for {dates[i]}."
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
                "location": "Delhi",
                "time": dates[i],

                "description": (
                    f"Maximum temperature of "
                    f"{max_temp}°C is forecast for "
                    f"{dates[i]}."
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
                "location": "Delhi",
                "time": dates[i],

                "description": (
                    f"Maximum temperature of "
                    f"{max_temp}°C is forecast for "
                    f"{dates[i]}."
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
            "location": "Delhi",
            "time": "Current",

            "description": (
                "No significant weather conditions "
                "meeting the WeatherGPT alert thresholds "
                "were detected."
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
            weather_data
        )

        return {
            "success": True,
            "source": "Open-Meteo",

            "official_warning": False,

            "message": (
                "WeatherGPT alerts generated from "
                "Open-Meteo weather and forecast data."
            ),

            "alerts": generated_alerts
        }

    except Exception as e:

        return {
            "success": False,
            "source": "Open-Meteo",
            "alerts": [],
            "message": (
                "Unable to generate weather alerts."
            ),
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


    # Temperature

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


    # Rainfall

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


    # Wind

    if wind_change > 15:

        effects.append(
            "Stronger winds may affect outdoor activities."
        )

        effects.append(
            "Loose objects may become a safety concern."
        )


    # Farming

    if (
        "farmer" in scenario_lower
        or "farming" in scenario_lower
    ):

        effects.append(
            "Farmers should monitor rainfall and "
            "temperature before irrigation or field operations."
        )


    # Travel

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

def impact_chain_analysis(weather_data):

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


    # Temperature

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


    # Rain

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


    # Wind

    if wind_speed >= 40:

        chain.append({
            "stage": "Wind",
            "event": "Strong winds",
            "impact": (
                "Outdoor safety concerns may increase."
            )
        })


    # Humidity

    if humidity >= 80:

        chain.append({
            "stage": "Humidity",
            "event": "High humidity",
            "impact": (
                "Perceived heat may increase."
            )
        })


    return {
        "location": "Delhi",
        "chain": chain
    }


# ============================================================
# CHAT API
# ============================================================

@app.post("/api/chat")
def chat(request: dict):

    message = request.get("message", "")
    message_lower = message.lower().strip()

    try:
        weather_data = get_weather_data()
    except Exception as e:
        return {
            "success": False,
            "reply": "I could not fetch the latest weather data.",
            "error": str(e)
        }

    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    apparent_temperature = current.get("apparent_temperature")
    precipitation = current.get("precipitation")
    wind_speed = current.get("wind_speed_10m")

    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    rainfall = daily.get("precipitation_sum", [])

    # Specific intents MUST come before generic "weather" and
    # "temperature" matching.


    # ---------------- ALERTS ----------------

    if (
        "alert" in message_lower
        or "warning" in message_lower
        or "warnings" in message_lower
        or "dangerous weather" in message_lower
        or "weather warning" in message_lower
    ):
        alert_data = generate_weather_alerts(weather_data)

        if not alert_data:
            reply = (
                "There are currently no WeatherGPT-generated "
                "weather alerts for Delhi."
            )
        else:
            reply = (
                f"I found {len(alert_data)} WeatherGPT-generated "
                f"weather alert(s) for Delhi based on the latest "
                f"weather and forecast data."
            )

        return {
            "success": True,
            "reply": reply,
            "type": "alerts",
            "data": {
                "source": "Open-Meteo",
                "official_warning": False,
                "alerts": alert_data
            }
        }


    # ---------------- DAY AFTER TOMORROW ----------------

    if (
        "day after tomorrow" in message_lower
        or "after tomorrow" in message_lower
    ) and len(dates) > 2:
        return {
            "success": True,
            "reply": (
                f"Day after tomorrow in Delhi, the expected "
                f"temperature range is {min_temps[2]}°C to "
                f"{max_temps[2]}°C. Expected precipitation is "
                f"{rainfall[2]} mm."
            ),
            "type": "forecast",
            "data": {
                "date": dates[2],
                "min_temperature": min_temps[2],
                "max_temperature": max_temps[2],
                "precipitation": rainfall[2]
            }
        }


    # ---------------- THREE DAYS FROM NOW ----------------
    # This MUST come before generic current-weather matching.
    #
    # Forecast index 3 means:
    # index 0 = today
    # index 1 = tomorrow
    # index 2 = day after tomorrow
    # index 3 = three days from today

    if (
        "in three days" in message_lower
        or "three days from now" in message_lower
        or "after three days" in message_lower
        or "three days later" in message_lower
        or "in 3 days" in message_lower
        or "3 days from now" in message_lower
        or "3 days later" in message_lower
        or "after 3 days" in message_lower
    ) and len(dates) > 3:

        index = 3

        return {
            "success": True,
            "reply": (
                f"Three days from now in Delhi, the expected "
                f"temperature range is {min_temps[index]}°C to "
                f"{max_temps[index]}°C. Expected precipitation is "
                f"{rainfall[index]} mm."
            ),
            "type": "forecast",
            "data": {
                "date": dates[index],
                "min_temperature": min_temps[index],
                "max_temperature": max_temps[index],
                "precipitation": rainfall[index]
            }
        }


    # ---------------- TOMORROW ----------------

    if "tomorrow" in message_lower and len(dates) > 1:
        return {
            "success": True,
            "reply": (
                f"Tomorrow in Delhi, the expected temperature "
                f"range is {min_temps[1]}°C to {max_temps[1]}°C. "
                f"Expected precipitation is {rainfall[1]} mm."
            ),
            "type": "forecast",
            "data": {
                "date": dates[1],
                "min_temperature": min_temps[1],
                "max_temperature": max_temps[1],
                "precipitation": rainfall[1]
            }
        }


    # ---------------- ONE WEEK / NEXT WEEK ----------------

    if (
        "one week later" in message_lower
        or "one week from now" in message_lower
        or "a week later" in message_lower
        or "next week" in message_lower
    ) and len(dates) >= 7:

        index = 6

        return {
            "success": True,
            "reply": (
                f"The latest available forecast day ({dates[index]}) "
                f"has an expected temperature range of "
                f"{min_temps[index]}°C to {max_temps[index]}°C, "
                f"with expected precipitation of {rainfall[index]} mm. "
                f"This is the last day currently available in the "
                f"7-day WeatherGPT forecast."
            ),
            "type": "forecast",
            "data": {
                "date": dates[index],
                "min_temperature": min_temps[index],
                "max_temperature": max_temps[index],
                "precipitation": rainfall[index]
            }
        }


    # ---------------- 7-DAY / WEEKLY FORECAST ----------------

    if (
        "7 day" in message_lower
        or "7-day" in message_lower
        or "seven day" in message_lower
        or "seven-day" in message_lower
        or "weekly forecast" in message_lower
        or "forecast" in message_lower
    ):
        forecast = [
            {
                "date": dates[i],
                "min_temperature": min_temps[i],
                "max_temperature": max_temps[i],
                "precipitation": rainfall[i]
            }
            for i in range(len(dates))
        ]

        return {
            "success": True,
            "reply": "Here is the 7-day weather forecast for Delhi.",
            "type": "forecast",
            "data": forecast
        }


    # ---------------- FARMING ----------------

    if (
        "farm" in message_lower
        or "farming" in message_lower
        or "farmer" in message_lower
        or "crop" in message_lower
    ):
        return {
            "success": True,
            "reply": (
                "For farming decisions, monitor temperature, rainfall, "
                "humidity and wind conditions. Avoid irrigation "
                "immediately before significant rainfall and monitor "
                "updated weather conditions."
            ),
            "type": "farming"
        }


    # ---------------- UMBRELLA ----------------

    if "umbrella" in message_lower:

        reply = (
            "Rainfall is currently present, so carrying an umbrella "
            "may be useful."
            if precipitation and precipitation > 0
            else "There is currently no significant rainfall in the current weather data."
        )

        return {
            "success": True,
            "reply": reply,
            "type": "decision"
        }


    # ---------------- CLOTHING ----------------

    if (
        "clothes" in message_lower
        or "clothing" in message_lower
        or "what should i wear" in message_lower
        or "what to wear" in message_lower
    ):
        if temperature >= 35:
            reply = (
                "Light and breathable clothing would generally be "
                "more comfortable in this temperature."
            )

        elif temperature <= 20:
            reply = "A light warm layer may be useful."

        else:
            reply = (
                "Normal comfortable clothing should be suitable "
                "for the current temperature."
            )

        return {
            "success": True,
            "reply": reply,
            "type": "decision"
        }


    # ---------------- OUTDOOR / WALK ----------------

    if (
        "walk" in message_lower
        or "go outside" in message_lower
        or "outside" in message_lower
    ):

        if temperature >= 38:

            reply = (
                "The temperature is quite high. Consider limiting "
                "prolonged outdoor activity and staying hydrated."
            )

        elif precipitation and precipitation > 0:

            reply = (
                "Rainfall is currently reported, so outdoor "
                "activities may be affected."
            )

        else:

            reply = (
                "Current weather conditions do not show a major "
                "weather-related obstacle to going outside."
            )

        return {
            "success": True,
            "reply": reply,
            "type": "decision"
        }


    # ---------------- WHAT-IF ----------------

    if (
        "what if" in message_lower
        or "what-if" in message_lower
    ):

        result = what_if_analysis(
            scenario=message,
            temperature_change=5,
            rainfall_change=10,
            wind_change=5,
            location="Delhi"
        )

        return {
            "success": True,
            "reply": "Here is the simulated impact of the weather scenario.",
            "type": "what_if",
            "data": result
        }


    # ---------------- IMPACT CHAIN ----------------

    if (
        "impact chain" in message_lower
        or "weather impact" in message_lower
        or "impact of weather" in message_lower
    ):

        result = impact_chain_analysis(weather_data)

        return {
            "success": True,
            "reply": "Here is the current weather impact chain.",
            "type": "impact_chain",
            "data": result
        }


    # ---------------- HUMIDITY ----------------

    if "humidity" in message_lower:

        return {
            "success": True,
            "reply": f"The current humidity in Delhi is {humidity}%.",
            "type": "humidity",
            "data": {
                "humidity": humidity
            }
        }


    # ---------------- WIND ----------------

    if "wind" in message_lower:

        return {
            "success": True,
            "reply": f"Current wind speed in Delhi is {wind_speed} km/h.",
            "type": "wind",
            "data": {
                "wind_speed": wind_speed
            }
        }


    # ---------------- RAIN ----------------

    if (
        "rain" in message_lower
        or "raining" in message_lower
        or "rainfall" in message_lower
    ):

        reply = (
            f"Rainfall is currently being reported at approximately "
            f"{precipitation} mm."
            if precipitation and precipitation > 0
            else "There is currently no significant rainfall reported "
                 "in the current weather data."
        )

        return {
            "success": True,
            "reply": reply,
            "type": "rain",
            "data": {
                "precipitation": precipitation
            }
        }


    # ---------------- CURRENT WEATHER ----------------
    # Generic matching is deliberately near the end.

    if (
        "weather" in message_lower
        or "temperature" in message_lower
        or "temp" in message_lower
        or "condition" in message_lower
        or "right now" in message_lower
        or "currently" in message_lower
        or "today" in message_lower
    ):

        return {
            "success": True,
            "reply": (
                f"Current weather in Delhi: {temperature}°C. "
                f"Feels like {apparent_temperature}°C. "
                f"Humidity is {humidity}%. "
                f"Wind speed is {wind_speed} km/h."
            ),
            "type": "weather",
            "data": {
                "temperature": temperature,
                "feels_like": apparent_temperature,
                "humidity": humidity,
                "precipitation": precipitation,
                "wind_speed": wind_speed
            }
        }


    # ---------------- DEFAULT ----------------

    return {
        "success": True,
        "reply": (
            "I can help with current weather, tomorrow's forecast, "
            "7-day forecasts, temperature, humidity, rainfall, wind, "
            "weather alerts, farming decisions, clothing, outdoor "
            "activities, What-If scenarios and weather impact analysis."
        ),
        "type": "general"
    }


# ============================================================
# MULTI-CITY WEATHER (MAP PAGE)
# ============================================================

CITIES = [
    {"name": "Delhi", "latitude": 28.6139, "longitude": 77.2090},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707},
    {"name": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946},
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867},
    {"name": "Ahmedabad", "latitude": 23.0225, "longitude": 72.5714},
    {"name": "Pune", "latitude": 18.5204, "longitude": 73.8567},
]


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

@app.get("/api/weather/cities")
def weather_cities():

    try:

        raw_data = get_multi_city_weather_data()

        if isinstance(raw_data, dict):
            raw_data = [raw_data]

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
                city_weather_data
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
        