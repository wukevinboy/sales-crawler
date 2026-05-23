import re
from dataclasses import dataclass, field

from src.utils.helpers import name_matches


@dataclass
class GooglePlayResult:
    app_id: str
    app_name: str
    rating: float | None
    review_count: int | None
    installs: str | None
    platform: str = "google_play"
    reviews: list[dict] = field(default_factory=list)


def _strict_name_match(query: str, candidate: str) -> bool:
    """Stricter match: query words must dominate the candidate title."""
    if not name_matches(query, candidate):
        return False
    q_words = [w for w in query.lower().split() if len(w) > 2]
    # Strip punctuation from candidate words for counting
    c_words = [w for w in re.sub(r"[^\w\s]", " ", candidate.lower()).split() if len(w) > 2]
    # Candidate should not have many more meaningful words than the query
    return len(c_words) <= max(2, len(q_words) * 2)


async def search_google_play(app_name: str, num_reviews: int = 30) -> GooglePlayResult | None:
    try:
        from google_play_scraper import Sort, app, reviews as gp_reviews, search

        results = search(app_name, lang="en", country="us", n_hits=10)
        valid = [r for r in results if r.get("appId")]
        if not valid:
            return None

        # Pick first result that strictly matches name AND has actual ratings
        match = next(
            (
                r for r in valid
                if _strict_name_match(app_name, r.get("title", ""))
                and (r.get("score") or 0) > 0
            ),
            None,
        )
        if match is None:
            return None

        app_id = match["appId"]

        try:
            details = app(app_id)
        except Exception:
            details = match

        review_list, _ = gp_reviews(
            app_id,
            lang="en",
            country="us",
            sort=Sort.MOST_RELEVANT,
            count=num_reviews,
        )

        reviews = [
            {
                "rating": r.get("score"),
                "content": r.get("content", ""),
                "author": r.get("userName", ""),
                "review_date": str(r.get("at", ""))[:10] if r.get("at") else None,
            }
            for r in review_list
        ]

        return GooglePlayResult(
            app_id=app_id,
            app_name=details.get("title") or match.get("title", app_name),
            rating=details.get("score") or match.get("score"),
            review_count=details.get("ratings") or match.get("ratings"),
            installs=details.get("installs") or match.get("installs"),
            reviews=reviews,
        )
    except Exception:
        return None
