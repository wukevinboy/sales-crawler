import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import Base


# --- Fixtures ---

@pytest.fixture(scope="function")
def test_app():
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from src.db.database import get_db
    from main import app

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# --- Tests ---

def test_health(test_app):
    resp = test_app.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["port"] == 5040


def test_root(test_app):
    resp = test_app.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_results_empty(test_app):
    resp = test_app.get("/results")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1


def test_get_result_not_found(test_app):
    resp = test_app.get("/results/nonexistent-id")
    assert resp.status_code == 404


def test_crawl_website_success(test_app):
    from src.crawlers.web_crawler import CrawlResult

    fake_result = CrawlResult(
        url="https://example-sales-ai.com",
        title="Example AI Sales Coach",
        description="AI-powered sales training",
        content_summary="Train your sales team with AI",
        keywords=["AI", "sales"],
        has_app=False,
    )

    with patch("src.api.routes.crawl.crawl_url", new=AsyncMock(return_value=fake_result)):
        resp = test_app.post(
            "/crawl/website",
            json={"url": "https://example-sales-ai.com", "analyze_apps": False},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["url"] == "https://example-sales-ai.com"
    assert data["title"] == "Example AI Sales Coach"
    assert data["has_app"] is False
    assert "id" in data


def test_crawl_website_fail(test_app):
    with patch("src.api.routes.crawl.crawl_url", new=AsyncMock(return_value=None)):
        resp = test_app.post(
            "/crawl/website",
            json={"url": "https://unreachable.example.com", "analyze_apps": False},
        )
    assert resp.status_code == 422


def test_crawl_website_stores_and_retrieves(test_app):
    from src.crawlers.web_crawler import CrawlResult

    fake_result = CrawlResult(
        url="https://salescoach-ai.com",
        title="SalesCoach AI | Best Sales Training",
        description="Train smarter",
        content_summary="Content here",
        keywords=["sales", "AI"],
        has_app=False,
    )

    with patch("src.api.routes.crawl.crawl_url", new=AsyncMock(return_value=fake_result)):
        post_resp = test_app.post(
            "/crawl/website",
            json={"url": "https://salescoach-ai.com", "analyze_apps": False},
        )

    website_id = post_resp.json()["id"]
    get_resp = test_app.get(f"/results/{website_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["url"] == "https://salescoach-ai.com"


def test_list_results_pagination(test_app):
    resp = test_app.get("/results?page=1&limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 5
    assert data["page"] == 1
