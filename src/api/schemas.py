from datetime import datetime
from typing import Any

from pydantic import BaseModel, HttpUrl


# --- Crawl ---

class CrawlWebsiteRequest(BaseModel):
    url: str
    analyze_apps: bool = True


class CrawlSearchRequest(BaseModel):
    keywords: list[str]
    max_pages: int = 5
    analyze_apps: bool = True


class CrawlResponse(BaseModel):
    id: str
    url: str
    title: str | None
    description: str | None
    has_app: bool
    crawled_at: datetime

    model_config = {"from_attributes": True}


# --- Analysis ---

class AnalyzeAppRequest(BaseModel):
    website_id: str
    app_name: str


class AppResponse(BaseModel):
    id: str
    website_id: str
    platform: str
    app_name: str | None
    app_id: str | None
    rating: float | None
    review_count: int | None
    installs: str | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


# --- Results ---

class ReviewResponse(BaseModel):
    id: str
    app_id: str
    rating: int | None
    content: str | None
    author: str | None
    review_date: str | None

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: str
    website_id: str
    competitor_summary: str | None
    review_highlights: dict | None
    market_insight: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebsiteDetailResponse(BaseModel):
    id: str
    url: str
    title: str | None
    description: str | None
    content_summary: str | None
    keywords: list[str] | None
    has_app: bool
    crawled_at: datetime
    apps: list[AppResponse] = []
    reports: list[ReportResponse] = []

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    items: list[Any]
