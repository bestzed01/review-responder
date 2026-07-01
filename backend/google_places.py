"""
Google Places API integration.

IMPORTANT LIMITATION to know going in: the Places API (Place Details
endpoint) returns AT MOST 5 reviews per place, and there's no way to
ask for more, paginate, or filter by "has the owner replied?" Google
doesn't expose reply status via this API at all.

This means: for v1, this gives you a great LIVE DEMO (show a business
owner real AI-drafted responses to their actual recent reviews), but
it does NOT give you a full "clear your entire backlog" tool. Be
upfront about that with customers — sell "I'll handle your new reviews
going forward" rather than "I'll fix your 200 unanswered reviews,"
unless you manually supplement with reviews you copy-pasted yourself.

You'll need a Google Cloud API key with the "Places API" enabled:
https://console.cloud.google.com/ -> APIs & Services -> enable "Places API"
-> Credentials -> Create API key
"""

import os
import httpx


def _get_api_key():
    return os.environ.get("GOOGLE_PLACES_API_KEY")

PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
FIND_PLACE_URL = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"


async def find_place_id(business_name: str, location_hint: str = "") -> dict:
    """
    Look up a place_id from a business name (+ optional location hint
    like 'Tashkent' to disambiguate). You'll use this once per business
    when onboarding them, then store the place_id so you don't need to
    search again.
    """
    query = f"{business_name} {location_hint}".strip()
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id,name,formatted_address",
        "key": _get_api_key(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(FIND_PLACE_URL, params=params)
        data = resp.json()

    if data.get("status") != "OK" or not data.get("candidates"):
        raise ValueError(f"No place found for '{query}'. Google status: {data.get('status')}")

    return data["candidates"][0]


async def fetch_reviews(place_id: str) -> list[dict]:
    """
    Fetch up to 5 reviews for a place. Returns a list of dicts with
    the fields we care about, already normalized into a shape that's
    easy to insert into our DB.
    """
    params = {
        "place_id": place_id,
        "fields": "name,rating,reviews",
        "key": _get_api_key(),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(PLACE_DETAILS_URL, params=params)
        data = resp.json()

    if data.get("status") != "OK":
        raise ValueError(f"Google Places error: {data.get('status')} - {data.get('error_message', '')}")

    raw_reviews = data.get("result", {}).get("reviews", [])

    reviews = []
    for r in raw_reviews:
        reviews.append({
            # Google doesn't give a stable review ID in this API, so we
            # build one from author + timestamp to dedupe on re-fetch.
            "google_review_id": f"{r.get('author_name', 'unknown')}_{r.get('time', 0)}",
            "author_name": r.get("author_name", "Anonymous"),
            "rating": r.get("rating", 0),
            "review_text": r.get("text", ""),
            "review_time": r.get("relative_time_description", ""),
        })
    return reviews
