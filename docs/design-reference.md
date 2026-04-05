# Design Reference: era.shopping

Источник вдохновения для лендинга geo-optimizer.

## Общий стиль
- Минимализм, high-contrast, premium B2B/SaaS эстетика
- Много whitespace
- Нумерованные секции (01, 02, 03...)
- Хэштег-лейблы для категоризации фич (#geo, #aeo, #reporting)
- Trademark/brand символ (®) — сигнализирует premium

## Структура страницы (5 секций)
1. **Hero** — главный хук + CTA
2. **Problem** — "почему это важно сейчас"
3. **Features** — 5 core capabilities (нумерованные карточки)
4. **Advantages** — сравнение с альтернативами
5. **Pricing + Contact**

## Маркетинговые хуки (брать как вдохновение, не копировать)
- "Own your presence in AI-generated answers"
- "AI answer engines are the new shopping front door"
- "If you aren't optimized for conversational models today, you're invisible tomorrow"
- "Win AI search in weeks, not months"

## CTAs (паттерны)
- Первичный: "Schedule a free assessment" / "Get free report" — низкий порог входа
- Вторичный: plan-specific кнопки

## Ценностные предложения era.shopping (для понимания рынка)
| Фича | Описание |
|------|----------|
| Visibility Tracking | Share-of-voice по моделям |
| Competitive Intel | Анализ конкурентов в AI |
| Query Discovery | Реальные запросы агентов |
| Content Engine | Автоматическая GEO-публикация |
| Technical SEO | Schema + crawlability |

## Ценообразование era.shopping (референс рынка)
- GEO Plan: $199/мес (Popular)
- Content Plan: $499/мес
- E-commerce: usage-based

→ Наш продукт должен быть в 10x дешевле для малого бизнеса ($9-29/мес)

## Наш адаптированный хук
"Тебя не находят в ChatGPT? Исправим за 5 минут — без программистов"

## UI компоненты для реализации
- Нумерованные feature-карточки
- Pricing table с toggle (monthly/yearly)
- Форма "вставь URL — получи анализ бесплатно"
- Таблица сравнения (мы vs агентство vs ничего)
- Newsletter/audit signup

---

## Точные дизайн-данные (извлечено через Playwright)

### Типографика
| Элемент | Font | Size | Weight | Letter-spacing |
|---------|------|------|--------|----------------|
| H1 | **Sora** | 170px | 800 | -8.5px |
| H2 | **Sora** | 96px | 700 | normal |
| Body | **Geist** | 12px+ | 500/600/700 | normal |
| Accent/mono | **IBM Plex Mono** | — | 500/700 italic | — |

Google Fonts: `Sora`, `Geist` (Vercel font), `IBM Plex Mono`

### Цвета
```css
/* Backgrounds */
--bg-light:   #E8E8E8;  /* основной фон body */
--bg-section: #F5F5F5;  /* секции на светлом */
--bg-dark:    #171717;  /* тёмные секции */
--bg-white:   #FFFFFF;

/* Text */
--text-dark:      #0E0E0E;
--text-gray:      #171717;
--text-white:     #FFFFFF;
--text-white-70:  rgba(255, 255, 255, 0.7);
```

### Скролл и анимации
- **Lenis** — smooth scroll библиотека (`lenis lenis-autoToggle`)
- **Framer Motion** — scroll-triggered анимации (reveal, stagger)
- Кнопки: `border-radius: 0px` (острые углы), padding `0 20px 0 28px`

### Реализация для нашего Next.js лендинга
```bash
npm install lenis @studio-freight/lenis framer-motion
```

```css
/* globals.css */
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@700;800&family=IBM+Plex+Mono:ital,wght@1,500;1,700&display=swap');
/* Geist — через next/font/google или vercel/geist */

:root {
  --bg-light: #E8E8E8;
  --bg-dark: #171717;
  --text-dark: #0E0E0E;
  --text-white: #FFFFFF;
  --text-white-70: rgba(255, 255, 255, 0.7);
}
```

## Анимации (по стилю Framer)
- Lenis smooth scroll
- Fade-in + translate при скролле (Framer Motion `whileInView`)
- Staggered reveal для карточек
- Hover эффекты на кнопках (scale/opacity)
- Number counter анимация для статистики
