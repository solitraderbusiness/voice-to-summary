import logging
import requests
from config.settings import OPENROUTER_API_KEY

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def summarize_text(text):
    try:
        logger.info("Starting summarization")
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"""
        گزارش مالی زیر را به صورت نکات کلیدی و مختصر به زبان فارسی خلاصه کنید. روی اطلاعات مهم و قابل اجرا تمرکز کنید و از تکرار جزئیات کم اهمیت خودداری کنید. خلاصه باید حدود ۲۰۰ کلمه باشد و با استفاده از Markdown (نقاط کلیدی با '- ' و متن مهم با **بولد**) و ایموجی‌های مرتبط (مانند 📈 برای افزایش قیمت، ⚠️ برای ریسک، ✅ برای توصیه) زیبا و جذاب باشد. اطمینان حاصل کنید که خلاصه خوانا و حرفه‌ای باشد.

        گزارش: {text}
        """
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,  # As per your change
            "temperature": 0.7
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            summary = response.json()["choices"][0]["message"]["content"].strip()
            logger.info(f"Summarization successful: {summary}")
            return summary
        else:
            error = response.text
            logger.error(f"Summarization error: {error}")
            return f"Summarization error: {error}"
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}", exc_info=True)
        return f"Summarization error: {str(e)}"
