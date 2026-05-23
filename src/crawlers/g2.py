import json
import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Known G2 product slugs for common sales tools
G2_SLUG_MAP = {
    "gong": "gong-io",
    "chorus": "chorus-ai",
    "salesloft": "salesloft",
    "mindtickle": "mindtickle",
    "second nature": "second-nature-ai",
    "hyperbound": "hyperbound",
    "yoodli": "yoodli",
    "saleshood": "saleshood",
    "wonderway": "wonderway",
}


@dataclass
class G2Result:
    app_id: str
    app_name: str
    rating: float | None
    review_count: int | None
    platform: str = "g2"
    reviews: list[dict] = field(default_factory=list)


def _find_slug(app_name: str) -> str:
    key = app_name.lower().strip()
    for k, v in G2_SLUG_MAP.items():
        if k in key or key in k:
            return v
    # Fallback: convert name to slug
    return re.sub(r"[^a-z0-9]+", "-", key).strip("-")


def _parse_rating(text: str) -> float | None:
    m = re.search(r"(\d+\.\d+|\d+)", text or "")
    return float(m.group(1)) if m else None


async def search_g2(app_name: str) -> G2Result | None:
    slug = _find_slug(app_name)
    url = f"https://www.g2.com/products/{slug}/reviews"

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        try:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
        except Exception:
            return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Try JSON-LD structured data first
    rating = None
    review_count = None
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                data = next((d for d in data if d.get("@type") == "Product"), {})
            agg = data.get("aggregateRating", {})
            if agg:
                rating = float(agg.get("ratingValue", 0)) or None
                review_count = int(agg.get("reviewCount", 0)) or None
                break
        except Exception:
            continue

    # Fallback: parse rating from page
    if not rating:
        r_el = soup.select_one("[itemprop=ratingValue], .fw-semibold.l2, .c-midnight-90")
        if r_el:
            rating = _parse_rating(r_el.get_text())

    # Parse reviews from page
    reviews = []
    for item in soup.select("[itemprop=review], .paper.paper--box"):
        body_el = item.select_one("[itemprop=reviewBody], .formatted-text p")
        rating_el = item.select_one("[itemprop=ratingValue]")
        author_el = item.select_one("[itemprop=author], .mb-0.fw-semibold")
        date_el = item.select_one("time")

        content = body_el.get_text(strip=True) if body_el else ""
        if not content or len(content) < 10:
            continue

        rev_rating = None
        if rating_el:
            rev_rating = _parse_rating(rating_el.get("content") or rating_el.get_text())

        reviews.append({
            "rating": int(rev_rating) if rev_rating else None,
            "content": content[:500],
            "author": author_el.get_text(strip=True) if author_el else None,
            "review_date": (date_el.get("datetime") or "")[:10] if date_el else None,
        })
        if len(reviews) >= 30:
            break

    if not rating and not reviews:
        return None

    return G2Result(
        app_id=slug,
        app_name=app_name,
        rating=rating,
        review_count=review_count or len(reviews),
        reviews=reviews,
    )
