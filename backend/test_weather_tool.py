from google import genai
from google.genai import types
import os


# ============================================================
# WEATHERGPT - GEMMA 4 FUNCTION CALLING TEST
# ============================================================

print()
print("==============================================")
print("WeatherGPT - Gemma 4 Tool Calling Test")
print("==============================================")


# ============================================================
# API KEY
# ============================================================

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:

    print()
    print("ERROR: GEMINI_API_KEY is not set.")
    print()
    print("Run:")
    print("$env:GEMINI_API_KEY='YOUR_API_KEY_HERE'")
    print()

    raise SystemExit(1)


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=api_key
)


# ============================================================
# WEATHER TOOL
# ============================================================

get_weather = {
    "name": "get_weather",
    "description": (
        "Gets live weather information for a requested "
        "city. Use this tool whenever the user asks about "
        "weather, temperature, rainfall, humidity, wind, "
        "forecast or outdoor weather conditions."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": (
                    "The city the user is asking about."
                )
            }
        },
        "required": [
            "location"
        ]
    }
}


# ============================================================
# TOOL CONFIGURATION
# ============================================================

tools = types.Tool(
    function_declarations=[
        get_weather
    ]
)


config = types.GenerateContentConfig(
    tools=[
        tools
    ],
    system_instruction=(
        "You are WeatherGPT, an intelligent weather assistant. "
        "Understand the user's question naturally. "
        "When the user asks for weather information, use "
        "the get_weather tool instead of inventing weather data. "
        "Do not guess live weather information."
    )
)


# ============================================================
# TEST QUESTION
# ============================================================

question = (
    "I am planning an outdoor event in Delhi. "
    "Can you check the weather for me?"
)


print()
print("User question:")
print(question)

print()
print("Sending question to Gemma 4...")
print()


# ============================================================
# SEND REQUEST
# ============================================================

try:

    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        contents=question,
        config=config
    )

except Exception as e:

    print()
    print("==============================================")
    print("REQUEST FAILED")
    print("==============================================")
    print()
    print(str(e))
    print()

    raise SystemExit(1)


# ============================================================
# CHECK FUNCTION CALL
# ============================================================

print()
print("==============================================")
print("GEMMA RESPONSE")
print("==============================================")
print()


if response.function_calls:

    print("SUCCESS!")
    print()
    print("Gemma decided that a weather tool is needed.")
    print()

    for function_call in response.function_calls:

        print("----------------------------------------------")

        print(
            "Function:",
            function_call.name
        )

        print(
            "Arguments:",
            function_call.args
        )

        print("----------------------------------------------")

    print()
    print("==============================================")
    print("FUNCTION CALLING WORKS")
    print("==============================================")
    print()
    print(
        "We can now connect Gemma to Open-Meteo."
    )
    print()

else:

    print(
        "Gemma did not request a weather tool."
    )

    print()

    print(
        "Model response:"
    )

    print(
        response.text
    )

    print()

    print("==============================================")
    print("NO FUNCTION CALL")
    print("==============================================")
    print()