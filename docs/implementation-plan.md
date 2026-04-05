# Implementation Plan: GEO Optimizer Backend

## Стек
- **FastAPI** (async) — REST API
- **SQLAlchemy 2.0** (async) + **Alembic** — ORM + миграции
- **asyncpg** — PostgreSQL драйвер
- **Celery** + **Redis** — очереди задач
- **Playwright** — краулер (async)
- **google-generativeai** — Gemini 3.0 Flash
- **boto3** — AWS Bedrock (Claude)
- **boto3** — Cloudflare R2 (S3-совместимый)
- **PropelAuth** — аутентификация
- **Docker Compose** — деплой

---

## Этапы реализации

### Этап 1: Project Foundation
1. `requirements.txt` — все зависимости
2. `app/core/config.py` — настройки из .env (pydantic-settings)
3. `app/core/database.py` — async SQLAlchemy engine + session
4. `app/core/storage.py` — Cloudflare R2 клиент
5. `app/main.py` — FastAPI app, роутеры, CORS, health check
6. `Dockerfile` + `docker-compose.yml` — backend + redis

### Этап 2: Database Models + Migrations
Модели:
- `User` — PropelAuth user_id, email, plan, created_at
- `Site` — url, domain, slug, user_id, status
- `SiteProfile` — name, description, business_type, address, phone, hours, social
- `SiteFile` — site_id, file_type (llms_txt/schema/faq/robots), content, r2_key, version
- `SiteReview` — site_id, source, rating, text, author, date
- `GenerationJob` — site_id, status, started_at, finished_at, error
- `MonitoringJob` — site_id, query, engine, status, scheduled_at
- `MonitoringResult` — job_id, site_id, engine, query, mentioned, position, snippet, checked_at

Alembic: init + первая миграция

### Этап 3: Task Queue (Celery + Redis)
- `app/worker.py` — Celery app init
- `app/tasks/crawl.py` — задача: запустить полный цикл по URL
- `app/tasks/generate.py` — задача: генерация файлов
- `app/tasks/monitor.py` — задача: проверить упоминания (еженедельно)
- `app/tasks/notify.py` — задача: отправить email отчёт

Флоу задачи:
```
crawl_site(url)
  → fetch_html + fetch_pdfs + fetch_images
  → fetch_reviews (Google Places)
  → ai_process(all_data)         # Gemini
  → generate_all_files()
  → save_to_db + upload_to_r2
  → build_profile_page()
  → index_now_ping()
  → notify_user()
```

### Этап 4: Crawler Module
`app/services/crawler/`
- `playwright_crawler.py` — async Playwright, JS-рендеринг
  - crawl_site(url) → CrawlResult(html, links, images, pdfs, meta, existing_schema)
  - Глубина: главная + /services, /about, /contacts, /products, /menu
- `html_parser.py` — BeautifulSoup, extract_meta(), extract_schema(), extract_contacts()

### Этап 5: Ingestion Module
`app/services/ingestion/`
- `gemini_vision.py`
  - process_pdf(pdf_bytes) → str (текст + структура)
  - process_image(image_url) → str (описание)
  - process_page_screenshot(page_url) → str
- `reviews_fetcher.py`
  - fetch_google_places(name, address) → List[Review]
  - fetch_2gis(name, city) → List[Review] (через Playwright)

### Этап 6: AI Processing Module
`app/services/ai/`
- `gemini_client.py` — async клиент Gemini 3.0 Flash
  - generate(prompt, context) → str
  - generate_structured(prompt, schema) → dict
- `claude_client.py` — boto3 Bedrock async
  - generate(prompt) → str
  - check_mention(business_name, query) → MentionResult
- `prompt_templates.py` — все промпты

### Этап 7: Generator Module
`app/services/generator/`
- `llms_txt.py` — build_llms_txt(profile, reviews, faq) → str
- `schema_builder.py` — build_json_ld(profile, reviews, type) → dict
- `faq_builder.py` — generate_faq(profile, business_type) → List[QA]
- `robots_patcher.py` — patch_robots_txt(existing) → str
- `zip_builder.py` — build_export_zip(site_id) → bytes

### Этап 8: API Endpoints
`app/api/v1/`
- `POST /analyze` — запустить анализ сайта (без auth, демо)
- `POST /sites` — создать сайт (с auth)
- `GET /sites/{id}` — получить профиль
- `GET /sites/{id}/files/{type}` — получить файл
- `GET /sites/{id}/export` — скачать ZIP
- `GET /sites/{id}/metrics` — метрики мониторинга
- `GET /profile/{slug}` — публичный профиль (для hosted page)

### Этап 9: Monitor Module
`app/services/monitor/`
- `google_checker.py` — Playwright → Google AI Overview проверка
- `claude_checker.py` — Claude API → прямой запрос, проверка упоминания
- `metrics_builder.py`
  - ai_visibility_score(site_id) → float (0-100)
  - mentions_timeline(site_id, days) → List[DataPoint]
  - competitor_mentions(query) → List[Competitor]
  - before_after(site_id) → BeforeAfter

### Этап 10: Docker + Deploy
- `Dockerfile` — multi-stage, Python 3.12
- `docker-compose.yml` — backend + celery_worker + redis
- `.github/workflows/deploy.yml` — CI/CD: push main → deploy to EC2
- SSL: certbot на сервере

---

## Структура файлов

```
backend/
├── app/
│   ├── main.py
│   ├── worker.py              # Celery
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── storage.py         # R2
│   ├── models/
│   │   ├── user.py
│   │   ├── site.py
│   │   ├── site_profile.py
│   │   ├── site_file.py
│   │   ├── site_review.py
│   │   └── monitoring.py
│   ├── api/
│   │   └── v1/
│   │       ├── analyze.py
│   │       ├── sites.py
│   │       └── monitor.py
│   ├── services/
│   │   ├── crawler/
│   │   │   ├── playwright_crawler.py
│   │   │   └── html_parser.py
│   │   ├── ingestion/
│   │   │   ├── gemini_vision.py
│   │   │   └── reviews_fetcher.py
│   │   ├── ai/
│   │   │   ├── gemini_client.py
│   │   │   ├── claude_client.py
│   │   │   └── prompt_templates.py
│   │   ├── generator/
│   │   │   ├── llms_txt.py
│   │   │   ├── schema_builder.py
│   │   │   ├── faq_builder.py
│   │   │   ├── robots_patcher.py
│   │   │   └── zip_builder.py
│   │   └── monitor/
│   │       ├── google_checker.py
│   │       ├── claude_checker.py
│   │       └── metrics_builder.py
│   └── tasks/
│       ├── crawl.py
│       ├── generate.py
│       ├── monitor.py
│       └── notify.py
├── alembic/
│   └── versions/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```
