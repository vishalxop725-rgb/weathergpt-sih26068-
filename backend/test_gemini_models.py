from google import genai
import os


# ============================================================
# WEATHERGPT - GEMINI MODEL AVAILABILITY TEST
# ============================================================

print()
print("==============================================")
print("WeatherGPT - Gemini Model Availability Test")
print("==============================================")


# ============================================================
# CHECK API KEY
# ============================================================

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:

    print()
    print("ERROR: GEMINI_API_KEY is not set.")
    print()
    print("Run this first:")
    print("$env:GEMINI_API_KEY='YOUR_API_KEY_HERE'")
    print()

    raise SystemExit(1)


print()
print("API key found.")
print("Connecting to Gemini...")
print()


# ============================================================
# CREATE CLIENT
# ============================================================

try:

    client = genai.Client(
        api_key=api_key
    )

except Exception as e:

    print("CLIENT CREATION FAILED")
    print()
    print(str(e))

    raise SystemExit(1)


# ============================================================
# GET AVAILABLE MODELS
# ============================================================

try:

    models = client.models.list()

except Exception as e:

    print()
    print("==============================================")
    print("COULD NOT LIST GEMINI MODELS")
    print("==============================================")
    print()
    print(str(e))
    print()

    raise SystemExit(1)


# ============================================================
# FIND TEXT GENERATION MODELS
# ============================================================

generation_models = []

print("Models available to your API key:")
print()


for model in models:

    supported_actions = getattr(
        model,
        "supported_actions",
        []
    )

    model_name = getattr(
        model,
        "name",
        ""
    )

    if "generateContent" in supported_actions:

        generation_models.append(model_name)

        print("----------------------------------------------")
        print(model_name)

        display_name = getattr(
            model,
            "display_name",
            None
        )

        if display_name:

            print(
                "Display name:",
                display_name
            )

        print(
            "Supports generateContent: YES"
        )


# ============================================================
# SUMMARY
# ============================================================

print()
print("==============================================")
print("MODEL LIST SUMMARY")
print("==============================================")

print()
print(
    "Number of text-generation models found:",
    len(generation_models)
)

print()


if not generation_models:

    print(
        "No model supporting generateContent "
        "was found for this API key."
    )

    print()

    raise SystemExit(1)


print("Now testing suitable text models...")
print()


# ============================================================
# PREFERRED MODELS
# ============================================================

preferred_models = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]


# ============================================================
# CREATE TEST ORDER
# ============================================================

test_models = []


for preferred in preferred_models:

    full_name = preferred

    if (
        full_name in generation_models
        and full_name not in test_models
    ):

        test_models.append(full_name)


# Add any other available generation model
# that wasn't in our preferred list.

for available in generation_models:

    if available not in test_models:

        test_models.append(available)


# ============================================================
# TEST MODELS
# ============================================================

successful_model = None


for model_name in test_models:

    print("----------------------------------------------")
    print("Testing:")
    print(model_name)

    try:

        response = client.models.generate_content(
            model=model_name,
            contents=(
                "You are testing WeatherGPT. "
                "Reply with exactly: Gemini is working."
            )
        )

        print()
        print("SUCCESS!")
        print()
        print("Response:")

        print(
            response.text
        )

        successful_model = model_name

        print()
        print("==============================================")
        print("WORKING GEMINI MODEL FOUND")
        print("==============================================")
        print()
        print(
            "Use this model in WeatherGPT:"
        )
        print()
        print(
            successful_model
        )
        print()

        break

    except Exception as e:

        print()
        print("FAILED")
        print()

        print(
            str(e)
        )

        print()


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("==============================================")
print("FINAL RESULT")
print("==============================================")


if successful_model:

    print()
    print("Gemini is available.")
    print()
    print(
        "Working model:",
        successful_model
    )
    print()

else:

    print()
    print(
        "No tested Gemini model responded successfully."
    )

    print()
    print(
        "The API key is recognized, but the available "
        "models are currently unavailable or restricted."
    )

    print()