# Instructions for Claude Code

## Model Preference
Use **Claude Sonnet 4.6** (model identifier: `claude-sonnet-4-6`) for this project.

## Project Overview
GEO-оптимизация сайтов под ИИ-поиск (ChatGPT, Perplexity, Яндекс ГПТ).
URL → парсинг → llms.txt + JSON-LD Schema + FAQ + hosted profile page.

## Tech Stack

### Frontend
- **Framework:** Next.js (TypeScript)
- **Repo:** https://github.com/SHADRINMMM/nextjs-landind (существующий, переделываем)
- **Хостинг:** Vercel
- **Дизайн-референс:** https://era.shopping/ — стиль нравится, берём вдохновение
- **Директория:** `frontend/`

### Backend
- **Framework:** FastAPI (Python)
- **Primary LLM:** Gemini 3.0 Flash (`gemini-3.0-flash`) via Google API
- **Деплой:** Docker
- **Директория:** `backend/`

### База данных
- **Вариант обсуждается:** Neon (serverless Postgres) vs self-hosted Postgres в Docker
- Решение: см. обсуждение в памяти

### Хранилище файлов
- **Cloudflare R2** (S3-совместимый)
- Bucket: `causabi`
- Endpoint: `https://af90042d625d670fc299183888ff935b.r2.cloudflarestorage.com`
- Public base URL: `https://pub-1e8b7f2f9aee4717b0f1792be20eba8e.r2.dev`
- Credentials: в `.env` файле (не коммитить!)

### Аутентификация
- **PropelAuth**

### Деплой
- Backend: Docker (хостинг обсуждается)
- Frontend: Vercel

## Структура проекта
```
geo-optimizer/
├── backend/          # FastAPI
├── frontend/         # Next.js
├── docs/
│   └── target-audience/   # Описания ЦА
└── CLAUDE.md
```

## Важные правила
- Credentials никогда не коммитить в git
- Все секреты только в .env файлах
- R2 credentials уже были показаны в открытом канале — нужно ротировать ключи
