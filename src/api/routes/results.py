from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.schemas import PaginatedResponse, WebsiteDetailResponse
from src.db.database import get_db
from src.db.models import App, Website

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_results(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    total_result = await db.execute(select(func.count(Website.id)))
    total = total_result.scalar_one()

    stmt = (
        select(Website)
        .options(selectinload(Website.apps), selectinload(Website.reports))
        .offset(offset)
        .limit(limit)
        .order_by(Website.crawled_at.desc())
    )
    result = await db.execute(stmt)
    websites = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        limit=limit,
        items=[WebsiteDetailResponse.model_validate(w) for w in websites],
    )


@router.get("/{website_id}", response_model=WebsiteDetailResponse)
async def get_result(website_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Website)
        .where(Website.id == website_id)
        .options(selectinload(Website.apps), selectinload(Website.reports))
    )
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return WebsiteDetailResponse.model_validate(website)


@router.get("/{website_id}/report")
async def get_report(website_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Website)
        .where(Website.id == website_id)
        .options(
            selectinload(Website.apps).selectinload(App.reviews),
            selectinload(Website.reports),
        )
    )
    result = await db.execute(stmt)
    website = result.scalar_one_or_none()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    return {
        "website_id": website_id,
        "url": website.url,
        "title": website.title,
        "apps": [
            {
                "platform": a.platform,
                "app_name": a.app_name,
                "rating": a.rating,
                "review_count": a.review_count,
                "installs": a.installs,
                "reviews": [
                    {"rating": r.rating, "content": r.content, "author": r.author, "review_date": r.review_date}
                    for r in a.reviews
                ],
            }
            for a in website.apps
        ],
        "reports": [
            {
                "competitor_summary": rp.competitor_summary,
                "review_highlights": rp.review_highlights,
                "market_insight": rp.market_insight,
                "created_at": rp.created_at.isoformat(),
            }
            for rp in sorted(website.reports, key=lambda r: r.created_at, reverse=True)
        ],
    }
