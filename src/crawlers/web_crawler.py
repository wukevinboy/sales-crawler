from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

from src.utils.helpers import clean_text, detect_app_links

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SEARCH_URL = "https://html.duckduckgo.com/html/"


@dataclass
class CrawlResult:
    url: str
    title: str | None = None
    description: str | None = None
    content_summary: str | None = None
    keywords: list[str] = field(default_factory=list)
    has_app: bool = False
    raw_html: str | None = None


async def fetch_page(url: str, timeout: int = 15) -> str | None:
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return None


def parse_page(url: str, html: str) -> CrawlResult:
    soup = BeautifulSoup(html, "lxml")

    title = None
    if soup.title:
        title = clean_text(soup.title.get_text())

    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    description = None
    if desc_tag and desc_tag.get("content"):
        description = clean_text(desc_tag["content"])

    # Extract first 500 chars of body text as summary
    body_text = clean_text(soup.get_text(separator=" "))
    content_summary = body_text[:500] if body_text else None

    # Keywords from meta
    kw_tag = soup.find("meta", attrs={"name": "keywords"})
    keywords = []
    if kw_tag and kw_tag.get("content"):
        keywords = [k.strip() for k in kw_tag["content"].split(",") if k.strip()]

    has_app = detect_app_links(html)

    return CrawlResult(
        url=url,
        title=title,
        description=description,
        content_summary=content_summary,
        keywords=keywords,
        has_app=has_app,
        raw_html=html,
    )


async def crawl_url(url: str) -> CrawlResult | None:
    html = await fetch_page(url)
    if not html:
        return None
    return parse_page(url, html)


async def search_and_crawl(keywords: list[str], max_pages: int = 5) -> list[CrawlResult]:
    query = " ".join(keywords)
    results: list[CrawlResult] = []

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        try:
            resp = await client.post(SEARCH_URL, data={"q": query, "b": ""})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select("a.result__a")
            urls = [a["href"] for a in links if a.get("href", "").startswith("http")]
        except Exception:
            return results

    for url in urls[:max_pages]:
        result = await crawl_url(url)
        if result:
            results.append(result)

    return results
