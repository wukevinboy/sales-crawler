from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import analysis, crawl, results
from src.db.database import init_db

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Sales Crawler",
    description="業務員 AI 對練競品調研爬蟲服務",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(crawl.router, prefix="/crawl", tags=["crawl"])
app.include_router(analysis.router, prefix="/analyze", tags=["analysis"])
app.include_router(results.router, prefix="/results", tags=["results"])


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/dashboard")
async def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "sales-crawler",
        "port": 5040,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5040, reload=True)
