import json
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import quote

from src.utils.helpers import name_matches


@dataclass
class AppStoreResult:
    app_id: str
    app_name: str
    rating: float | None
    review_count: int | None
    platform: str = "app_store"
    reviews: list[dict] = field(default_factory=list)


def _itunes_search(app_name: str, country: str = "us") -> dict | None:
    url = (
        f"https://itunes.apple.com/search?term={quote(app_name)}"
        f"&country={country}&entity=software&limit=10"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        for res in results:
            track_name = res.get("trackName", "")
            # Must name-match AND have actual user ratings
            if name_matches(app_name, track_name) and res.get("userRatingCount", 0) > 0:
                return res
    except Exception:
        pass
    return None


def _itunes_reviews(app_id: str, country: str = "us") -> list[dict]:
    url = (
        f"https://itunes.apple.com/{country}/rss/customerreviews"
        f"/id={app_id}/sortBy=mostRecent/json"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        entries = data.get("feed", {}).get("entry", [])
        reviews = []
        for e in entries[1:]:
            reviews.append({
                "rating": int(e.get("im:rating", {}).get("label", 0)),
                "content": e.get("content", {}).get("label", ""),
                "author": e.get("author", {}).get("name", {}).get("label", ""),
                "review_date": e.get("updated", {}).get("label", "")[:10],
            })
        return reviews
    except Exception:
        return []


async def search_app_store(app_name: str, country: str = "us") -> AppStoreResult | None:
    app_info = _itunes_search(app_name, country)
    if not app_info:
        return None

    app_id = str(app_info.get("trackId", ""))
    reviews = _itunes_reviews(app_id, country)

    return AppStoreResult(
        app_id=app_id,
        app_name=app_info.get("trackName", app_name),
        rating=app_info.get("averageUserRating"),
        review_count=app_info.get("userRatingCount"),
        reviews=reviews,
    )
