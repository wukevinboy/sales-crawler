# Sales Crawler

> 業務員 AI 對練 — 競品調研爬蟲服務

針對「AI 銷售培訓 / 業務員 AI 對練」市場，自動爬取競品網站、抓取 App Store 與 Google Play 評論，並彙整競品分析、用戶評論、市場洞察，透過內建 Dashboard 一覽無遺。

---

## 功能特色

- **網站爬取** — 以關鍵字或指定 URL 爬取競品網站，提取標題、描述、內容摘要
- **App 市場分析** — 自動抓取 App Store (iOS) 與 Google Play 的評分、評論數、用戶評論
- **競品報告** — 自動生成競品摘要、市場洞察、正負面評論關鍵字
- **視覺化 Dashboard** — 左右分欄介面，含 Overview / Reviews / Analysis 三個 Tab
- **REST API** — 所有功能皆可透過 API 調用，方便整合至其他系統

---

## 快速開始

**環境需求：** Python 3.11+

```bash
# 1. 建立虛擬環境
python3.11 -m venv .venv && source .venv/bin/activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 安裝 Playwright 瀏覽器（JS 渲染 fallback 用）
playwright install chromium

# 4. 啟動服務（port 5040）
uvicorn main:app --host 0.0.0.0 --port 5040 --reload
```

啟動後開啟瀏覽器：[http://localhost:5040](http://localhost:5040)

健康檢查：`GET http://localhost:5040/health`

---

## 專案結構

```
sales-crawler/
├── main.py                     # FastAPI 入口，port 5040
├── requirements.txt
├── .env.example                # 環境變數範本
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── crawl.py        # POST /crawl/website、/crawl/search
│   │   │   ├── analysis.py     # POST /analyze/app
│   │   │   └── results.py      # GET  /results、/results/{id}
│   │   └── schemas.py          # Pydantic request / response models
│   ├── crawlers/
│   │   ├── web_crawler.py      # httpx + BeautifulSoup4 通用爬蟲
│   │   ├── app_store.py        # iTunes Search API
│   │   ├── google_play.py      # google-play-scraper
│   │   └── product_hunt.py     # Product Hunt 爬蟲
│   ├── analyzers/
│   │   ├── competitor.py       # 競品摘要生成
│   │   ├── review_summary.py   # 評論關鍵字分析
│   │   └── market.py           # 市場洞察生成
│   ├── db/
│   │   ├── database.py         # SQLAlchemy 2.0 async engine
│   │   └── models.py           # ORM models (Website / App / Review / AnalysisReport)
│   └── utils/
│       └── helpers.py          # URL 正規化、品牌名稱推斷
├── static/
│   └── index.html              # 競品 Dashboard
└── tests/
    ├── test_crawlers.py
    ├── test_analyzers.py
    └── test_api.py
```

---

## API 參考

| Method | Path | 說明 |
|--------|------|------|
| GET | `/health` | 服務狀態 |
| GET | `/` | Dashboard 介面 |
| POST | `/crawl/website` | 爬取指定 URL |
| POST | `/crawl/search` | 以關鍵字搜尋並批次爬取 |
| POST | `/analyze/app` | 觸發 App 市場分析 |
| GET | `/results` | 分頁查詢所有競品結果 |
| GET | `/results/{id}` | 查詢單筆網站資料 |
| GET | `/results/{id}/report` | 查詢完整競品分析報告 |

### 使用範例

```bash
# 以關鍵字搜尋競品
curl -X POST http://localhost:5040/crawl/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI sales roleplay", "業務員 AI 對練"],
    "max_pages": 5,
    "analyze_apps": true
  }'

# 觸發指定網站的 App 市場分析
curl -X POST http://localhost:5040/analyze/app \
  -H "Content-Type: application/json" \
  -d '{"website_id": "<id>", "app_name": "Gong"}'

# 查看完整競品報告
curl http://localhost:5040/results/<id>/report
```

---

## 資料庫 Schema

| 資料表 | 說明 |
|--------|------|
| `websites` | 爬取的競品網站基本資料 |
| `apps` | 各平台 App 資訊（評分、下載量） |
| `reviews` | 抓取的用戶評論 |
| `analysis_reports` | 自動生成的競品分析報告 |

預設使用 SQLite，存放於 `./data/sales_crawler.db`。
如需切換 PostgreSQL，在 `.env` 設定 `DATABASE_URL`。

---

## 開發指令

```bash
# 執行所有測試
pytest tests/ -v

# 含覆蓋率報告
pytest tests/ --cov=src --cov-report=term-missing
```

---

## 技術棧

| 類別 | 套件 |
|------|------|
| Web Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| 資料庫 | SQLite / PostgreSQL |
| 爬蟲 | httpx + BeautifulSoup4 |
| JS 渲染 | Playwright (Chromium) |
| App Store | iTunes Search API |
| Google Play | google-play-scraper |
| 資料驗證 | Pydantic v2 |

---

## 注意事項

- 爬蟲使用 DuckDuckGo HTML 搜尋介面，免費且無需 API key
- App Store 搜尋使用官方 iTunes Search API（非第三方套件）
- G2.com 因 Cloudflare 保護目前無法自動爬取
- 請遵守各平台的使用條款與爬取頻率限制
