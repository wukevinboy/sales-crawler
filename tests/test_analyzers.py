from src.analyzers.competitor import build_competitor_summary
from src.analyzers.market import build_market_insight
from src.analyzers.review_summary import summarize_reviews


def test_summarize_reviews_empty():
    result = summarize_reviews([])
    assert result["total"] == 0
    assert result["avg_rating"] is None


def test_summarize_reviews_basic():
    reviews = [
        {"rating": 5, "content": "excellent product love it"},
        {"rating": 5, "content": "excellent service very good"},
        {"rating": 1, "content": "terrible broken app"},
    ]
    result = summarize_reviews(reviews)
    assert result["total"] == 3
    assert result["avg_rating"] == pytest.approx(11 / 3, 0.01)
    assert "excellent" in result["positive"]
    assert "terrible" in result["negative"]


def test_build_competitor_summary_no_results():
    summary = build_competitor_summary("TestApp", [])
    assert "TestApp" in summary
    assert "未找到" in summary


def test_build_market_insight_no_results():
    insight = build_market_insight([])
    assert "不足" in insight


import pytest
