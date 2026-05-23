from collections import defaultdict

THEMES: dict[str, list[str]] = {
    "易用性": ["easy", "intuitive", "simple", "user-friendly", "smooth", "clean", "straightforward"],
    "AI 品質": ["ai", "realistic", "natural", "accurate", "smart", "lifelike", "human-like", "believable"],
    "Coaching 回饋": ["feedback", "coaching", "improvement", "tips", "suggestions", "actionable", "advice"],
    "功能完整": ["features", "comprehensive", "complete", "powerful", "integration", "customiz", "flexible"],
    "費用": ["expensive", "price", "cost", "pricing", "affordable", "worth", "cheap", "subscription", "paid"],
    "技術問題": ["bug", "crash", "glitch", "slow", "freeze", "error", "broken", "lag", "issue", "problem"],
    "客服": ["support", "response", "help", "team", "service", "customer", "reply", "contact"],
    "練習效果": ["practice", "improve", "skill", "confidence", "real-world", "result", "better", "progress"],
}


def _sentences(text: str) -> list[str]:
    import re
    return [s.strip() for s in re.split(r"[.!?\n]+", text) if len(s.strip()) > 20]


def _theme_counts(reviews: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for rev in reviews:
        content = (rev.get("content") or "").lower()
        for theme, keywords in THEMES.items():
            if any(kw in content for kw in keywords):
                counts[theme] += 1
    return dict(counts)


def analyze_review_insights(reviews: list[dict]) -> dict:
    if not reviews:
        return {
            "praised": [],
            "complaints": [],
            "advantages": [],
            "pain_points": [],
            "review_base": 0,
        }

    positive = [r for r in reviews if (r.get("rating") or 0) >= 4]
    negative = [r for r in reviews if (r.get("rating") or 5) <= 2]

    praised_counts = _theme_counts(positive)
    complaint_counts = _theme_counts(negative)

    praised = sorted(
        [{"theme": t, "count": c} for t, c in praised_counts.items()],
        key=lambda x: -x["count"],
    )[:5]
    complaints = sorted(
        [{"theme": t, "count": c} for t, c in complaint_counts.items()],
        key=lambda x: -x["count"],
    )[:5]

    advantages: list[str] = []
    seen: set[str] = set()
    for rev in sorted(positive, key=lambda r: -(r.get("rating") or 0)):
        content = (rev.get("content") or "").lower()
        for keywords in THEMES.values():
            for sent in _sentences(rev.get("content") or ""):
                if any(kw in sent.lower() for kw in keywords):
                    key = sent[:60]
                    if key not in seen and len(advantages) < 5:
                        seen.add(key)
                        advantages.append(sent[:120])
        if len(advantages) >= 5:
            break

    pain_points: list[str] = []
    seen2: set[str] = set()
    for rev in sorted(negative, key=lambda r: (r.get("rating") or 5)):
        content = (rev.get("content") or "").lower()
        for keywords in THEMES.values():
            for sent in _sentences(rev.get("content") or ""):
                if any(kw in sent.lower() for kw in keywords):
                    key = sent[:60]
                    if key not in seen2 and len(pain_points) < 5:
                        seen2.add(key)
                        pain_points.append(sent[:120])
        if len(pain_points) >= 5:
            break

    return {
        "praised": praised,
        "complaints": complaints,
        "advantages": advantages,
        "pain_points": pain_points,
        "review_base": len(reviews),
    }
