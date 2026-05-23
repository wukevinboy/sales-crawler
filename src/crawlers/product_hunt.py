from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


@dataclass
class ProductHuntResult:
    app_id: str
    app_name: str
    rating: float | None
    review_count: int | None
    platform: str = "product_hunt"
    reviews: list[dict] = field(default_factory=list)


async def search_product_hunt(app_name: str) -> ProductHuntResult | None:
    query = app_name.replace(" ", "+")
    url = f"https://www.producthunt.com/search?q={query}"

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
        except Exception:
            return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Try to find first product result
    product_links = soup.select("a[href*='/posts/']")
    if not product_links:
        return None

    first_href = product_links[0].get("href", "")
    product_url = f"https://www.producthunt.com{first_href}" if first_href.startswith("/") else first_href

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15) as client:
        try:
            resp = await client.get(product_url)
            resp.raise_for_status()
        except Exception:
            return None

    soup = BeautifulSoup(resp.text, "lxml")

    # Extract vote count as proxy for rating
    vote_el = soup.select_one("[data-test*=vote], .vote-count, [class*=voteCount]")
    vote_count = None
    if vote_el:
        try:
            vote_count = int(vote_el.get_text().strip().replace(",", ""))
        except ValueError:
            pass

    # Extract comments/reviews
    comments = soup.select("[class*=comment] p, [class*=review] p")
    reviews = [
        {
            "rating": None,
            "content": c.get_text(strip=True),
            "author": None,
            "review_date": None,
        }
        for c in comments[:20]
        if c.get_text(strip=True)
    ]

    product_name = soup.find("h1")
    name = product_name.get_text(strip=True) if product_name else app_name

    return ProductHuntResult(
        app_id=first_href.replace("/posts/", "").strip("/"),
        app_name=name,
        rating=None,
        review_count=vote_count,
        reviews=reviews,
    )
