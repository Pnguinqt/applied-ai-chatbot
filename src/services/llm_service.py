
from google import genai
from google.genai import types
import time

from src.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    validate_config,
)


def generate_response(
    history: list,
    system_instruction: str,
) -> str:
    """
    Sends conversation history to Gemini and returns its response.
    """

    validate_config()

    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"[Gemini] Using model: {GEMINI_MODEL}", flush=True)

    contents = [
        {
            "role": "user" if message["role"] == "user" else "model",
            "parts": [{"text": message["content"]}],
        }
        for message in history
    ]

    start_time = time.perf_counter()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=1000,
            temperature=0.7,
        ),
    )

    elapsed = time.perf_counter() - start_time

    print(
        f"[Gemini] Response received in {elapsed:.3f} seconds",
        flush=True
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text
