from collections import Counter

STOPWORDS = {
    "the","and","for","this","that","with","have","been","they","from",
    "you","your","not","are","was","can","but","all","our","its","has",
    "it's","app","use","can't","also","very","will","more","when","just",
    "there","their","into","than","some","these","each","him","her","his",
    "she","him","over","after","who","had","him","did","one","two",
    "i'm","i've","i'll","don't","didn't","isn't","hasn't","it's","he's","she's",
    "The","App","It's","they're","we're","you're",
}

def summarize_reviews(reviews: list[dict]) -> dict:
    if not reviews:
        return {"positive": [], "negative": [], "avg_rating": None, "total": 0}

    ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    positive_kw: Counter = Counter()
    negative_kw: Counter = Counter()

    for review in reviews:
        content = review.get("content") or ""
        rating = review.get("rating")
        words = [
            w.strip(".,!?;:\'\"-()[]") for w in content.split()
            if len(w.strip(".,!?;:\'\"-()[]")) > 3
            and w.strip(".,!?;:\'\"-()[]").lower() not in STOPWORDS
            and not w.startswith("http")
        ]
        if rating is not None:
            if rating >= 4:
                positive_kw.update(w.lower() for w in words)
            elif rating <= 2:
                negative_kw.update(w.lower() for w in words)

    return {
        "avg_rating": avg_rating,
        "total": len(reviews),
        "positive": [w for w, _ in positive_kw.most_common(12)],
        "negative": [w for w, _ in negative_kw.most_common(12)],
    }
