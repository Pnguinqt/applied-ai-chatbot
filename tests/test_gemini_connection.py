
from google import genai

from src.core.config import GEMINI_API_KEY, validate_config


def test_gemini_connection():
    validate_config()

    client = genai.Client(api_key=GEMINI_API_KEY)

    print("\nAvailable Gemini models:")

    models = client.models.list()

    for model in models:
        actions = model.supported_actions or []

        if "generateContent" in actions:
            print(f"- {model.name}")


if __name__ == "__main__":
    test_gemini_connection()
