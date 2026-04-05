# Architecture: GEO Optimizer

## Принцип
**1 URL от пользователя → полный цикл автоматически**

Все обращения к внешним источникам — через мультимодальное API (Gemini 3.0 Flash).
Claude (Bedrock) — мониторинг упоминаний + fallback для генерации.

---

## Модули системы

```
┌─────────────────────────────────────────────────────┐
│                    USER INPUT                        │
│                   [ URL сайта ]                      │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              1. INGESTION LAYER                      │
│  Crawler → PDF/Image Vision → Reviews API            │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              2. AI PROCESSING                        │
│   Gemini 3.0 Flash (multimodal) — primary            │
│   Claude Bedrock — monitoring + fallback             │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              3. GENERATION LAYER                     │
│  llms.txt │ JSON-LD │ FAQ │ robots.txt │ Profile      │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              4. STORAGE                              │
│     Neon (PostgreSQL) │ Cloudflare R2                │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              5. DELIVERY                             │
│  API │ Download ZIP │ Hosted Page │ WP Plugin        │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│              6. MONITOR + METRICS                    │
│  Google AI │ Claude check │ Dashboard │ Email        │
└─────────────────────────────────────────────────────┘
```

---

## Модуль 1: Ingestion Layer

### 1.1 Crawler
**Задача:** Извлечь всё что есть на сайте.

**Open Source:**
- `Playwright` (Python) — JS-рендеринг, работает с SPA
- `BeautifulSoup4` — парсинг HTML
- `Firecrawl` (open source) — готовый scraper с markdown output, можно self-host

**Что извлекаем:**
- Название, описание, контакты, адрес, часы работы
- Список страниц (из sitemap или обходом)
- Существующий schema.org (JSON-LD в head)
- Open Graph метаданные
- Изображения (ссылки → передаём в Vision)
- Ссылки на PDF (меню, прайс, каталог)

**Глубина:** главная + до 10 ключевых страниц (services, about, contacts, products)

### 1.2 Мультимодальная обработка
**Задача:** Прочитать нестандартные форматы через Gemini Vision.

**Gemini 3.0 Flash API:**
- PDF → текст + структура (меню, прайс → список товаров/услуг с ценами)
- Изображения → описание (витрина, интерьер, продукция)
- Скриншоты сайта → понять структуру если HTML плохой

**Prompt стратегия:**
```
"Ты анализируешь бизнес. Вот [PDF/изображение].
Извлеки: название, тип бизнеса, список услуг/товаров с описаниями и ценами,
контактные данные, особенности. Верни JSON."
```

### 1.3 Reviews & External Data
**Задача:** Обогатить профиль отзывами и рейтингами.

**Источники:**
- **Google Places API** (бесплатно 1000 req/мес) — рейтинг, отзывы, часы, фото
- **Яндекс.Карты** — парсинг через Playwright (официального API нет для РФ)
- **2ГИС API** (есть бесплатный тир) — локальный бизнес РФ

**Что берём:**
- Общий рейтинг (звёзды)
- Топ-10 отзывов (для Review schema.org)
- Категория бизнеса
- Популярные часы посещения (если есть)

---

## Модуль 2: AI Processing

**Primary: Gemini 3.0 Flash** (Google API)
- Мультимодальность (текст + изображения + PDF)
- Быстрый, дешёвый
- Используем для: генерации контента, обработки файлов

**Secondary: Claude (AWS Bedrock)**
- Для мониторинга: спрашиваем Claude напрямую через API
- Fallback для генерации если Gemini недоступен
- Точнее для структурированного вывода

**Промпт-шаблоны (хранятся в БД, версионируются):**
- `system_prompt_business_profile` — генерация профиля бизнеса
- `system_prompt_faq` — генерация FAQ под нишу
- `system_prompt_schema` — валидация и улучшение schema.org
- `system_prompt_monitor` — анализ упоминаний в ответе ИИ

---

## Модуль 3: Generation Layer

### 3.1 llms.txt Generator
```markdown
# {Business Name}
> {Short description, 1-2 sentences}

## About
{Full description}

## Services/Products
- {item 1}: {description}
- {item 2}: {description}

## FAQ
- Q: {question}  A: {answer}

## Contact
- Address: {address}
- Phone: {phone}
- Hours: {hours}
```

### 3.2 JSON-LD Schema Generator
Типы schema по типу бизнеса:
- `LocalBusiness` → рестораны, салоны, клиники
- `Store` → магазины
- `MedicalOrganization` → клиники
- `FoodEstablishment` → рестораны
- `FAQPage` → для FAQ блока
- `Review` → из отзывов

### 3.3 robots.txt Patch
Добавляем разрешение для AI-ботов:
```
User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /
```

### 3.4 IndexNow
**Бесплатный API** от Bing/Yandex — моментальное уведомление об обновлении.
После генерации страницы → отправляем IndexNow → быстрая индексация.

---

## Модуль 4: Storage

**Neon PostgreSQL:**
```sql
sites (id, user_id, url, domain, created_at, updated_at)
site_profiles (id, site_id, business_name, description, business_type, ...)
site_files (id, site_id, file_type, content, r2_key, version, created_at)
site_reviews (id, site_id, source, rating, text, created_at)
monitoring_results (id, site_id, query, engine, mentioned, position, response_text, checked_at)
```

**Cloudflare R2:**
- `sites/{site_id}/llms.txt`
- `sites/{site_id}/schema.json`
- `sites/{site_id}/faq.html`
- `sites/{site_id}/original_pdf/{filename}`

---

## Модуль 5: Delivery

**5.1 Hosted Profile Page**
URL: `ai.causabi.com/b/{slug}`
- Рендерится как Next.js SSG/SSR
- JSON-LD в head
- FAQ разметка
- Индексируется AI-ботами (наш домен растёт в авторитете)

**5.2 API**
```
POST /api/v1/analyze     → запустить анализ сайта
GET  /api/v1/sites/{id}  → получить профиль
GET  /api/v1/sites/{id}/files/llms.txt
GET  /api/v1/sites/{id}/files/schema.json
GET  /api/v1/sites/{id}/export → ZIP со всеми файлами
```

**5.3 WordPress Plugin**
- PHP плагин → обращается к нашему API
- Автоматически ставит schema.json в head
- Создаёт/обновляет llms.txt в корне
- Добавляет FAQ блок на нужные страницы

---

## Модуль 6: Monitor + Metrics

### Что мониторим
**Google AI (AI Overviews):**
- Playwright запрашивает Google с нужным запросом
- Проверяет наличие упоминания в AI Overview блоке
- Open source: `serpapi` (бесплатно 100 req/мес) или прямой Playwright

**Claude (Bedrock):**
- Прямой API запрос: "Какой лучший [тип бизнеса] в [городе]?"
- Проверяем упоминается ли наш клиент
- Записываем: да/нет, позиция, контекст упоминания

**Perplexity:**
- Через Playwright (нет официального API для проверки)
- Или через их search API если есть

### Метрики для клиента (пруфы что работаем)

```
📊 AI Visibility Score (0-100)
   — % запросов где упомянуты / всего запросов

📈 Mentions Timeline
   — график упоминаний по неделям

🔍 Query Coverage
   — какие запросы приводят к упоминанию

🤖 Engine Breakdown
   — Google AI / Claude / Perplexity отдельно

📋 Before/After
   — сравнение: до установки vs сейчас

🏆 Competitor Comparison
   — кто ещё упоминается по тем же запросам
```

**Техническая метрика:**
- llms.txt: есть/нет, последнее обновление
- Schema.org: типы, валидность
- robots.txt: разрешены ли AI-боты
- IndexNow: дата последней отправки

---

## Внешние API и Open Source

| Инструмент | Назначение | Цена |
|-----------|-----------|------|
| **Firecrawl** (OSS) | Web scraping → markdown | Self-host бесплатно |
| **Playwright** (OSS) | JS рендеринг, мониторинг | Бесплатно |
| **Google Places API** | Отзывы, рейтинг, часы | 1000 req/мес бесплатно |
| **2ГИС API** | Локальный бизнес РФ | Есть бесплатный тир |
| **IndexNow API** | Моментальная индексация | Бесплатно |
| **SerpAPI** | Результаты Google поиска | 100 req/мес бесплатно |
| **schema-dts** (NPM) | TypeScript типы для schema.org | Бесплатно |
| **Gemini 3.0 Flash** | Основной AI (мультимодальный) | Pay-per-use |
| **Claude (Bedrock)** | Мониторинг + fallback | Pay-per-use |

---

## Стек реализации

```
backend/
├── app/
│   ├── api/           # FastAPI роуты
│   ├── services/
│   │   ├── crawler/   # Playwright + BeautifulSoup
│   │   ├── ingestion/ # PDF, images → Gemini Vision
│   │   ├── reviews/   # Google Places, 2GIS
│   │   ├── ai/        # Gemini + Claude клиенты
│   │   ├── generator/ # llms.txt, schema, FAQ, robots
│   │   ├── delivery/  # API, ZIP, profile
│   │   └── monitor/   # AI query checker + metrics
│   ├── models/        # SQLAlchemy модели
│   └── core/          # config, db, storage (R2)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
