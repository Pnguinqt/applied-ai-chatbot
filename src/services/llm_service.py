
from google import genai

from src.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    validate_config,
)


def generate_response(prompt: str) -> str:
    """
    Sends a user's prompt to Gemini and returns its response.
    """

    validate_config()

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text
