import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    content_summary: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[dict | None] = mapped_column(JSON)
    has_app: Mapped[bool] = mapped_column(Boolean, default=False)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    apps: Mapped[list["App"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    reports: Mapped[list["AnalysisReport"]] = relationship(back_populates="website", cascade="all, delete-orphan")


class App(Base):
    __tablename__ = "apps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    website_id: Mapped[str] = mapped_column(ForeignKey("websites.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    app_name: Mapped[str | None] = mapped_column(Text)
    app_id: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    installs: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    website: Mapped["Website"] = relationship(back_populates="apps")
    reviews: Mapped[list["Review"]] = relationship(back_populates="app", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    app_id: Mapped[str] = mapped_column(ForeignKey("apps.id"), nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(Text)
    review_date: Mapped[str | None] = mapped_column(String(10))

    app: Mapped["App"] = relationship(back_populates="reviews")


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    website_id: Mapped[str] = mapped_column(ForeignKey("websites.id"), nullable=False)
    competitor_summary: Mapped[str | None] = mapped_column(Text)
    review_highlights: Mapped[dict | None] = mapped_column(JSON)
    market_insight: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    website: Mapped["Website"] = relationship(back_populates="reports")
