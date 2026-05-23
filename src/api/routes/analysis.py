import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analyzers.competitor import build_competitor_summary
from src.analyzers.market import build_market_insight
from src.analyzers.review_insights import analyze_review_insights
from src.analyzers.review_summary import summarize_reviews
from src.analyzers.website_content import analyze_website_content
from src.api.schemas import AnalyzeAppRequest
from src.crawlers.app_store import search_app_store
from src.crawlers.g2 import search_g2
from src.crawlers.google_play import search_google_play
from src.crawlers.product_hunt import search_product_hunt
from src.db.database import get_db
from src.db.models import AnalysisReport, App, Review, Website

router = APIRouter()


@router.post("/app")
async def analyze_app(req: AnalyzeAppRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(Website).where(Website.id == req.website_id)
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    app_name = req.app_name

    ios_result, play_result, ph_result, g2_result = await asyncio.gather(
        search_app_store(app_name),
        search_google_play(app_name),
        search_product_hunt(app_name),
        search_g2(app_name),
        return_exceptions=True,
    )

    platform_results = []
    for platform, res in [
        ("app_store", ios_result),
        ("google_play", play_result),
        ("product_hunt", ph_result),
        ("g2", g2_result),
    ]:
        if isinstance(res, Exception) or res is None:
            continue
        platform_results.append((platform, res))

        existing_q = await db.execute(
            select(App).where(App.website_id == website.id, App.platform == platform)
        )
        existing_app = existing_q.scalar_one_or_none()

        if existing_app:
            await db.execute(delete(Review).where(Review.app_id == existing_app.id))
            existing_app.app_name     = res.app_name
            existing_app.app_id       = res.app_id
            existing_app.rating       = res.rating
            existing_app.review_count = res.review_count
            existing_app.installs     = getattr(res, "installs", None)
            app_record = existing_app
        else:
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

    all_reviews = [rev for _, res in platform_results for rev in res.reviews]

    competitor_summary = build_competitor_summary(app_name, platform_results)
    review_highlights = summarize_reviews(all_reviews)
    market_insight = build_market_insight(platform_results)
    insights = analyze_review_insights(all_reviews)

    await db.execute(
        delete(AnalysisReport).where(AnalysisReport.website_id == website.id)
    )

    report = AnalysisReport(
        website_id=website.id,
        competitor_summary=competitor_summary,
        review_highlights=review_highlights,
        market_insight=market_insight,
        insights_json=insights,
    )
    db.add(report)
    await db.commit()

    return {
        "website_id": website.id,
        "app_name": app_name,
        "platforms_analyzed": [p for p, _ in platform_results],
        "report_id": report.id,
        "review_count": len(all_reviews),
        "competitor_summary": competitor_summary,
        "review_highlights": review_highlights,
        "market_insight": market_insight,
    }


@router.post("/website/{website_id}/content")
async def analyze_website_content_endpoint(
    website_id: str, db: AsyncSession = Depends(get_db)
):
    stmt = select(Website).where(Website.id == website_id)
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    data = analyze_website_content(
        title=website.title or "",
        description=website.description or website.content_summary or "",
    )
    website.summary_zh = data["summary_zh"]
    website.features_zh = data["features_zh"]
    await db.commit()
    return {"status": "ok", "website_id": website_id, "summary_zh": website.summary_zh}
