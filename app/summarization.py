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
        گزارش مالی زیر را به صورت نکات کلیدی و دقیق به زبان فارسی خلاصه کنید. فقط اطلاعات موجود در متن را خلاصه کنید و از افزودن اطلاعات خارجی یا حدس و گمان خودداری کنید. خلاصه باید حدود ۳۰۰ کلمه (۲۵۰–۳۵۰ کلمه) باشد و در سه بخش **اطلاعات کلی**، **رویدادها و تحلیل**، و **توصیه‌ها و سهام** سازماندهی شود. نکات زیر را رعایت کنید:
        - تاریخ ذکرشده در ابتدای گزارش را در بخش **اطلاعات کلی** با ایموجی 🗓️ بیاورید.
        - برای هر ادعا یا وضعیت (مانند افزایش ارزش معاملات)، دلیل ذکرشده در متن را با عبارت **به دلیل** بیاورید.
        - اعداد (مانند درصد، قیمت، حجم) را دقیقاً همان‌طور که در متن آمده گزارش کنید (مثلاً ۰٫۷۳ درصد، نه ۷۵ همت).
        - بخش‌هایی که در متن به‌عنوان **مهم** علامت‌گذاری شده‌اند، با جزئیات بیشتری (۲–۳ جمله) توضیح دهید.
        - تمام اسامی سهام یا نهادهای ذکرشده (مانند بانک اقتصاد نوین، فولاد مبارکه) را دقیقاً در خلاصه بیاورید.
        هر بخش شامل نقاط کلیدی با جملات کوتاه (۱۰–۲۰ کلمه) باشد، مگر در نقاط مهم که نیاز به توضیح بیشتر دارند. از MarkdownV2 (نقاط کلیدی با '- '، متن مهم با **بولد**، سرفصل‌ها با ###، فاصله مناسب بین بخش‌ها) و ایموجی‌های مرتبط (📈 برای افزایش، 📉 برای کاهش، ⚠️ برای ریسک، ✅ برای توصیه، 🚨 برای رویداد، 🗓️ برای تاریخ، 📊 برای اعداد، 💡 برای نکات مهم) استفاده کنید. خلاصه باید خوانا، حرفه‌ای، و جذاب باشد.

        گزارش: {text}
        """
        payload = {
            "model": "openai/gpt-4.1-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1500,  # For ~300 words
            "temperature": 0.0  # For fidelity
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
