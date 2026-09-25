import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models_to_try = [os.getenv("GEMINI_MODEL", "gemini-3.8-flash")]

for model in models_to_try:

    print("=" * 50)
    print(f"Testing: {model}")
    print("=" * 50)

    try:

        response = client.models.generate_content(
            model=model,
            contents="Explain digital forensics in one simple sentence."
        )

        print("SUCCESS")
        print(response.text)

        break

    except Exception as error:

        print("FAILED")
        print(error)
