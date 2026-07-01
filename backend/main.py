"""
Main FastAPI app. This is the file that WIRES TOGETHER the three
pieces you just built:
  database.py      -> stores businesses + reviews + drafts
  google_places.py -> fetches real reviews from Google
  claude_drafter.py -> turns a review into a drafted response

The pattern to notice: each route does three things in order:
  1. Read from DB (or call an external API)
  2. Do some logic
  3. Write back to DB / return JSON

That's basically the entire shape of backend web development.

Run this with:
    cd backend
    venv/bin/uvicorn main:app --reload --port 8000

--reload means it restarts automatically when you save a file change,
which you want during development.
"""

import secrets
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_db
import google_places
import claude_drafter

app = FastAPI()

# CORS: by default, browsers block your React frontend (running on
# e.g. localhost:5173) from calling your backend (localhost:8000)
# because they're "different origins." This middleware tells the
# browser "it's fine, allow it." In production you'd restrict
# allow_origins to your real frontend domain instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Runs once when the server starts. Creates tables if they don't exist.
init_db()


@app.post("/api/businesses")
async def create_business(business_name: str, location_hint: str = ""):
    """
    Onboard a new business. You (not the business owner) call this
    once per customer when you sign them up. It:
      1. Looks up their Google place_id by name
      2. Generates a random slug for their dashboard link
      3. Saves them to the DB
      4. Returns the dashboard link you'll send them
    """
    try:
        place = await google_places.find_place_id(business_name, location_hint)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # secrets.token_urlsafe generates an unguessable random string —
    # this is what makes "no login needed" an acceptable shortcut.
    # Don't use this approach for anything more sensitive than review drafts.
    slug = f"biz_{secrets.token_urlsafe(6)}"

    with get_db() as conn:
        conn.execute(
            "INSERT INTO businesses (slug, name, google_place_id) VALUES (?, ?, ?)",
            (slug, place["name"], place["place_id"]),
        )

    return {
        "slug": slug,
        "name": place["name"],
        "address": place.get("formatted_address", ""),
        "dashboard_url": f"/dashboard/{slug}",
    }


@app.post("/api/businesses/{slug}/refresh")
async def refresh_reviews(slug: str):
    """
    Pull the latest reviews from Google for this business, draft a
    response for any review we haven't seen before, and save both.
    This is the core pipeline. Call it when a business owner opens
    their dashboard, or on a schedule later (e.g. once a day).
    """
    with get_db() as conn:
        business = conn.execute(
            "SELECT * FROM businesses WHERE slug = ?", (slug,)
        ).fetchone()

    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    reviews = await google_places.fetch_reviews(business["google_place_id"])

    new_count = 0
    with get_db() as conn:
        for r in reviews:
            existing = conn.execute(
                "SELECT id FROM reviews WHERE business_id = ? AND google_review_id = ?",
                (business["id"], r["google_review_id"]),
            ).fetchone()

            if existing:
                continue  # already have this one, skip drafting again

            drafted = claude_drafter.draft_response(
                review_text=r["review_text"],
                rating=r["rating"],
                author_name=r["author_name"],
                business_name=business["name"],
            )

            conn.execute(
                """INSERT INTO reviews
                   (business_id, google_review_id, author_name, rating,
                    review_text, review_time, drafted_response)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (business["id"], r["google_review_id"], r["author_name"],
                 r["rating"], r["review_text"], r["review_time"], drafted),
            )
            new_count += 1

    return {"new_reviews_drafted": new_count}


@app.get("/api/businesses/{slug}/reviews")
async def get_reviews(slug: str):
    """
    What the dashboard calls to display everything. Pure read —
    no external API calls, just returns what's already in our DB.
    """
    with get_db() as conn:
        business = conn.execute(
            "SELECT * FROM businesses WHERE slug = ?", (slug,)
        ).fetchone()

        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        reviews = conn.execute(
            "SELECT * FROM reviews WHERE business_id = ? ORDER BY id DESC",
            (business["id"],),
        ).fetchall()

    return {
        "business_name": business["name"],
        "reviews": [dict(r) for r in reviews],
    }


@app.patch("/api/reviews/{review_id}")
async def update_drafted_response(review_id: int, drafted_response: str):
    """
    Lets the business owner edit a draft before copying it. Small
    but important: it makes the tool feel like theirs, not a black box.
    """
    with get_db() as conn:
        conn.execute(
            "UPDATE reviews SET drafted_response = ? WHERE id = ?",
            (drafted_response, review_id),
        )
    return {"ok": True}
