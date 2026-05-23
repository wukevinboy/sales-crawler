import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import CrawlResponse, CrawlSearchRequest, CrawlWebsiteRequest
from src.crawlers.web_crawler import crawl_url, search_and_crawl
from src.db.database import get_db
from src.db.models import AnalysisReport, App, Review, Website
from src.utils.helpers import infer_app_name, normalize_url

router = APIRouter()


async def _save_crawl_result(website_data: dict, db: AsyncSession) -> Website:
    existing = await db.execute(select(Website).where(Website.url == website_data["url"]))
    website = existing.scalar_one_or_none()
    if website:
        for k, v in website_data.items():
            setattr(website, k, v)
    else:
        website = Website(**website_data)
        db.add(website)
    await db.commit()
    await db.refresh(website)
    return website


async def _run_app_analysis(website: Website, db: AsyncSession) -> None:
    from src.analyzers.competitor import build_competitor_summary
    from src.analyzers.market import build_market_insight
    from src.analyzers.review_summary import summarize_reviews
    from src.crawlers.app_store import search_app_store
    from src.crawlers.google_play import search_google_play
    from src.crawlers.product_hunt import search_product_hunt

    app_name = infer_app_name(website.title, website.url)

    ios_result, play_result, ph_result = await asyncio.gather(
        search_app_store(app_name),
        search_google_play(app_name),
        search_product_hunt(app_name),
        return_exceptions=True,
    )

    platform_results = []
    for platform, res in [
        ("app_store", ios_result),
        ("google_play", play_result),
        ("product_hunt", ph_result),
    ]:
        if isinstance(res, Exception) or res is None:
            continue
        platform_results.append((platform, res))

        app_record = App(
            website_id=website.id,
            platform=platform,
            app_name=res.app_name,
            app_id=res.app_id,
            rating=res.rating,
            review_count=res.review_count,
            installs=getattr(res, "installs", None),
        )
        db.add(app_record)
        await db.flush()

        for rev in res.reviews:
            db.add(
                Review(
                    app_id=app_record.id,
                    rating=rev.get("rating"),
                    content=rev.get("content"),
                    author=rev.get("author"),
                    review_date=rev.get("review_date"),
                )
            )

    if not platform_results:
        await db.commit()
        return

    all_reviews = [rev for _, res in platform_results for rev in res.reviews]
    db.add(
        AnalysisReport(
            website_id=website.id,
            competitor_summary=build_competitor_summary(app_name, platform_results),
            review_highlights=summarize_reviews(all_reviews),
            market_insight=build_market_insight(platform_results),
        )
    )
    await db.commit()


@router.post("/website", response_model=CrawlResponse)
async def crawl_website(req: CrawlWebsiteRequest, db: AsyncSession = Depends(get_db)):
    url = normalize_url(req.url)
    result = await crawl_url(url)
    if not result:
        raise HTTPException(status_code=422, detail=f"Failed to crawl {url}")

    website = await _save_crawl_result(
        {
            "url": result.url,
            "title": result.title,
            "description": result.description,
            "content_summary": result.content_summary,
            "keywords": result.keywords,
            "has_app": result.has_app,
        },
        db,
    )

    if req.analyze_apps:
        await _run_app_analysis(website, db)

    return CrawlResponse.model_validate(website)


@router.post("/search", response_model=list[CrawlResponse])
async def crawl_search(req: CrawlSearchRequest, db: AsyncSession = Depends(get_db)):
    results = await search_and_crawl(req.keywords, max_pages=req.max_pages)
    if not results:
        return []

    saved = []
    for r in results:
        website = await _save_crawl_result(
            {
                "url": r.url,
                "title": r.title,
                "description": r.description,
                "content_summary": r.content_summary,
                "keywords": r.keywords,
                "has_app": r.has_app,
            },
            db,
        )
        if req.analyze_apps:
            await _run_app_analysis(website, db)
        saved.append(CrawlResponse.model_validate(website))
    return saved
