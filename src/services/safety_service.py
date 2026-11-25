
import re


# Common prompt-injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"act\s+as\s+(a\s+)?(different|new|another)\s+(AI|assistant|model)",
    r"bypass\s+(your\s+)?(rules|restrictions|instructions|safety)",
    r"override\s+(your\s+)?(system\s+)?instructions",
]


def check_input_safety(prompt: str) -> tuple[bool, str]:
    """
    Checks user input for common prompt-injection attempts.

    Returns:
        (True, "") if the input is allowed.
        (False, rejection_message) if an injection pattern is detected.
    """

    if not prompt or not prompt.strip():
        return False, "Please enter a message."

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            return (
                False,
                "I can't follow instructions that attempt to override "
                "my system rules or reveal internal instructions. "
                "I'm here to help with computer hardware questions."
            )

    return True, ""
