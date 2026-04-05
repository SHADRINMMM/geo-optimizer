"""
Multimodal processing via Gemini 3.0 Flash — PDFs, images, screenshots.
"""
import base64
import httpx
from app.core.config import get_settings

settings = get_settings()


async def process_pdf_url(pdf_url: str) -> str:
    """Download PDF and extract structured content via Gemini Vision."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(pdf_url)
        pdf_bytes = resp.content

    return await process_pdf_bytes(pdf_bytes)


async def process_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract structured content from PDF via Gemini multimodal."""
    import google.generativeai as genai
    genai.configure(api_key=settings.GOOGLE_API_KEY)

    model = genai.GenerativeModel(settings.LLM_MODEL)

    prompt = """Ты анализируешь PDF-документ бизнеса (меню, прайс-лист, каталог товаров или услуг).

Извлеки и верни в формате JSON:
{
  "document_type": "menu|price_list|catalog|other",
  "items": [
    {
      "name": "название товара/услуги",
      "description": "описание если есть",
      "price": "цена если есть",
      "category": "категория если есть"
    }
  ],
  "notes": "важные особенности или акции если есть"
}

Если это меню — извлеки все блюда/напитки с ценами.
Если прайс — все услуги с ценами.
Верни только JSON без markdown."""

    pdf_part = {
        "inline_data": {
            "mime_type": "application/pdf",
            "data": base64.b64encode(pdf_bytes).decode("utf-8"),
        }
    }

    response = model.generate_content([prompt, pdf_part])
    return response.text


async def process_image_url(image_url: str) -> str:
    """Describe business image via Gemini Vision."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(image_url)
        image_bytes = resp.content
        content_type = resp.headers.get("content-type", "image/jpeg")

    return await process_image_bytes(image_bytes, content_type)


async def process_image_bytes(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Describe image content for business context."""
    import google.generativeai as genai
    genai.configure(api_key=settings.GOOGLE_API_KEY)

    model = genai.GenerativeModel(settings.LLM_MODEL)

    prompt = """Опиши это изображение в контексте бизнеса (магазин, ресторан, офис, продукция и т.д.).
Укажи: что изображено, атмосфера/стиль, видимые товары/услуги, особенности интерьера/экстерьера.
Ответ на русском, 2-3 предложения."""

    image_part = {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        }
    }

    response = model.generate_content([prompt, image_part])
    return response.text
