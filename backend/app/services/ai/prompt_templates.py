"""
Centralized prompt templates for all AI operations.
"""

BUILD_PROFILE_PROMPT = """Ты эксперт по оптимизации бизнеса для AI-поиска (GEO — Generative Engine Optimization).

Тебе дана информация о сайте бизнеса. Твоя задача — создать максимально полный и точный профиль бизнеса,
оптимизированный для того чтобы ChatGPT, Perplexity и другие ИИ-поисковики рекомендовали этот бизнес пользователям.

ДАННЫЕ С САЙТА:
{crawl_data}

ОТЗЫВЫ:
{reviews}

Верни JSON строго по схеме:
{{
  "business_name": "официальное название",
  "description": "подробное описание бизнеса 3-5 предложений, включая уникальные особенности",
  "short_description": "1-2 предложения для быстрого ответа ИИ",
  "business_type": "тип по schema.org: LocalBusiness|Store|Restaurant|MedicalOrganization|etc",
  "business_category": "категория: restaurant|salon|clinic|shop|service|etc",
  "address": "полный адрес",
  "city": "город",
  "phone": "телефон",
  "email": "email",
  "hours": "часы работы",
  "products_services": [
    {{
      "name": "название",
      "description": "описание",
      "price": "цена или null",
      "category": "категория"
    }}
  ],
  "faq": [
    {{"question": "вопрос который задают пользователи", "answer": "подробный ответ"}}
  ],
  "target_queries": [
    "запрос1 который пользователи вводят в ChatGPT для поиска такого бизнеса",
    "запрос2",
    "запрос3",
    "запрос4",
    "запрос5"
  ],
  "unique_features": ["особенность1", "особенность2"],
  "instagram": "url или null",
  "vk": "url или null",
  "telegram_channel": "url или null"
}}

FAQ должен содержать 8-12 вопросов которые реально задают пользователи в ИИ-чатах.
target_queries — запросы на том языке на котором говорят клиенты бизнеса (русский или английский).
products_services — ВСЕ товары/услуги которые удалось найти, максимально подробно.
Верни только JSON без markdown."""


FAQ_GENERATION_PROMPT = """Создай 10 вопросов и ответов для {business_type} под названием "{business_name}".

Контекст бизнеса: {description}

Требования к вопросам:
- Реальные вопросы которые люди задают в ChatGPT и Perplexity
- Охватывают: что предлагает, цены, расположение, особенности, отличия
- На {language}

Верни JSON массив:
[{{"question": "...", "answer": "подробный ответ 2-3 предложения"}}]

Только JSON, без markdown."""


MONITOR_ANALYSIS_PROMPT = """Проанализируй ответ ИИ-поисковика на запрос пользователя.

Запрос пользователя: "{query}"
Наш бизнес: "{business_name}"
Наши товары/услуги: {products}

Ответ ИИ:
{ai_response}

Определи:
1. Упоминается ли наш бизнес "{business_name}"? (true/false)
2. На какой позиции упоминается (1 = первое место, null если не упоминается)?
3. Цитата из ответа где упоминается наш бизнес (или null)?
4. Какие из наших товаров/услуг упоминаются?
5. Какие конкурирующие бизнесы упоминаются?

Верни JSON:
{{
  "mentioned": true/false,
  "position": 1/2/3/null,
  "snippet": "цитата или null",
  "product_mentions": [{{"product": "название", "mentioned": true/false, "context": "цитата или null"}}],
  "competitors": ["конкурент1", "конкурент2"]
}}

Только JSON."""
