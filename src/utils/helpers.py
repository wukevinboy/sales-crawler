import re
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    return parsed.geturl()


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_app_links(html: str) -> bool:
    patterns = [
        r"apps\.apple\.com",
        r"play\.google\.com/store/apps",
        r"producthunt\.com",
        r"app-store",
        r"google-play",
    ]
    return any(re.search(p, html, re.IGNORECASE) for p in patterns)


def infer_app_name(title: str | None, url: str) -> str:
    domain_name = extract_domain(url).replace("www.", "").split(".")[0]

    if title:
        cleaned = title
        for sep in ["|", "-", "\u2013", ":", "\u00b7"]:
            if sep in cleaned:
                cleaned = cleaned.split(sep)[0].strip()
                break
        # Long descriptive titles (>4 words) are not brand names; use domain
        if len(cleaned.split()) > 4:
            return domain_name.title()
        return cleaned.strip()

    return domain_name.title()


def name_matches(query: str, candidate: str) -> bool:
    """Check if a search query is a reasonable match for a result title."""
    q = query.lower()
    c = candidate.lower()
    q_words = [w for w in q.split() if len(w) > 2]
    if not q_words:
        return False
    # All query words must appear in candidate (word-boundary match)
    return all(re.search(r"\b" + re.escape(w) + r"\b", c) for w in q_words)
