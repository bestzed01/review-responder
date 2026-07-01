"""
Gemini API integration for drafting review responses.

Using Gemini's free tier (Flash model) instead of a paid API, since
this is v1 / proof-of-concept stage. Swap to a paid model later once
there's revenue to justify it — the rest of the app doesn't care
which model drafts the text, since this file's function signature
stays the same either way.

Get a free key at aistudio.google.com (no credit card needed).
"""

import os
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You write short, warm, professional responses from a \
business owner to a customer review. Match the language the review was \
written in (Uzbek, Russian, or English). Keep it under 60 words. \
Thank the reviewer by name if given. For positive reviews, express \
genuine appreciation. For negative reviews, acknowledge the issue \
without being defensive, and invite them to reach out directly to \
resolve it. Never sound robotic or generic. Output ONLY the response \
text, nothing else — no preamble, no quotes around it."""


def draft_response(review_text: str, rating: int, author_name: str, business_name: str) -> str:
    user_message = f"""Business name: {business_name}
Reviewer: {author_name}
Star rating: {rating}/5
Review text: "{review_text}"

Write the response."""

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=user_message,
        config={"system_instruction": SYSTEM_PROMPT},
    )

    return response.text.strip()
