# Sales Crawler

業務員 AI 對練競品調研爬蟲服務。運行在 **port 5040**。

## Quick Start

```bash
# 1. 建立虛擬環境
python3 -m venv .venv && source .venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 安裝 Playwright 瀏覽器（JS 渲染 fallback 用）
playwright install chromium

# 4. 啟動
uvicorn main:app --host 0.0.0.0 --port 5040 --reload
```

Health check: `GET http://localhost:5040/health`

## Architecture

```
sales-crawler/
├── main.py                  # FastAPI entry, port 5040
├── src/
│   ├── api/routes/          # crawl.py / analysis.py / results.py
│   ├── crawlers/            # web_crawler, app_store, google_play, product_hunt
│   ├── analyzers/           # competitor, review_summary, market
│   ├── db/                  # SQLAlchemy async (SQLite)
│   └── utils/               # helpers
├── tests/
└── data/                    # SQLite DB 存放位置
```

## API Reference

| Method | Path | 說明 |
|--------|------|------|
| GET | `/health` | 服務狀態 |
| POST | `/crawl/website` | 爬取指定 URL |
| POST | `/crawl/search` | 關鍵字搜尋並爬取 |
| POST | `/analyze/app` | 觸發 App 市場分析 |
| GET | `/results` | 分頁查詢所有結果 |
| GET | `/results/{id}` | 查詢單筆網站資料 |
| GET | `/results/{id}/report` | 查詢完整分析報告 |

### 爬取並分析範例

```bash
# Step 1: 以關鍵字搜尋
curl -X POST http://localhost:5040/crawl/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["AI sales roleplay", "業務員 AI 對練"], "max_pages": 5, "analyze_apps": true}'

# Step 2: 取得 website_id，觸發 App 分析
curl -X POST http://localhost:5040/analyze/app \
  -H "Content-Type: application/json" \
  -d '{"website_id": "<id>", "app_name": "SalesCoach AI"}'

# Step 3: 查看報告
curl http://localhost:5040/results/<id>/report
```

## Development

```bash
# 執行測試
pytest tests/ -v

# 執行單一測試
pytest tests/test_crawlers.py -v
```

## Notes

- 爬蟲使用 DuckDuckGo HTML 搜尋介面（免費，無需 API key）
- App Store 分析依賴 `app-store-scraper` 套件
- Google Play 分析依賴 `google-play-scraper` 套件
- SQLite DB 存放於 `./data/sales_crawler.db`
- 如需 PostgreSQL，設定 `.env` 中的 `DATABASE_URL`
