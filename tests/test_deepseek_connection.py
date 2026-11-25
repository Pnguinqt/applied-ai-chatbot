from openai import OpenAI

from src.core.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    validate_config,
)


def test_deepseek_connection():
    validate_config()

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )

    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "user", "content": "Reply with: DeepSeek connection successful."}
        ],
        max_tokens=30,
    )

    answer = response.choices[0].message.content
   

    assert answer, "DeepSeek returned an empty response."

    print("\nDeepSeek connection successful!")
    print(f"Model: {DEEPSEEK_MODEL}")
    print(f"Response: {answer}")


if __name__ == "__main__":
    test_deepseek_connection()