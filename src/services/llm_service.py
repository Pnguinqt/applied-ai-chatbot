
from openai import OpenAI
import time

from src.core.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    validate_config,
)


def generate_response(
    history: list,
    system_instruction: str,
) -> str:
    """
    Sends conversation history to DeepSeek and returns its response.
    """

    validate_config()

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )

    print(f"[DeepSeek] Using model: {DEEPSEEK_MODEL}", flush=True)

    messages = [
        {"role": "system", "content": system_instruction}
    ]

    for message in history:
        messages.append({
            "role": message["role"],
            "content": message["content"],
        })

    start_time = time.perf_counter()

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages,
        max_tokens=1000,
        temperature=0.7,
    )

    elapsed = time.perf_counter() - start_time

    print(
        f"[DeepSeek] Response received in {elapsed:.3f} seconds",
        flush=True
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("DeepSeek returned an empty response.")

    return answer
