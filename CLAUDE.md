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

## Где смотреть
- Все ключи и credentials: `backend/.env` (не в git)
- Шаблон переменных: `backend/.env.example`
- ЦА и дистрибуция: `docs/target-audience/`
- Скиллы (deploy, db, etc.): `.claude/skills/`

## Сервисы и доступы
| Сервис | Описание |
|--------|----------|
| AWS EC2 | 98.89.42.222, ubuntu, ключ `causa.pem` в coffee-shop-platform |
| Neon | Serverless Postgres, eu-central-1 |
| Cloudflare R2 | Bucket `causabi` |
| Gemini | 3.0 Flash, `GOOGLE_API_KEY` |
| AWS Bedrock | `AWS_BEDROCK_API_KEY` |
| PropelAuth | Auth, новый env под ai.causabi.com |
| PostHog | Аналитика, project 144288 |
| Vercel | Фронт (Next.js) |
| GitHub | https://github.com/SHADRINMMM/geo-optimizer |

## Важные правила
- Credentials никогда не коммитить в git
- Все секреты только в .env файлах
- Для деплоя использовать skill: `/deploy-backend`
- Для работы с БД использовать skill: `/db`
