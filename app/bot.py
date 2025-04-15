import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN
from app.transcription import transcribe_audio
from app.summarization import summarize_text
from app.database import save_report
import os
import uuid
import asyncio
import re

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

transcription_lock = asyncio.Lock()

def escape_markdown_v2(text):
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r'([_\*\[\]()~`>#+\-=|{}.!\\])'  # Include period and backslash
    return re.sub(special_chars, r'\\\1', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    logger.info(f"Received /start command from user {user_id}")
    await update.message.reply_text("لطفاً یک پیام صوتی ارسال کنید تا آن را خلاصه کنم\\!", parse_mode="MarkdownV2")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        logger.info(f"Received voice message from user {user_id}")

        if not update.message.voice:
            logger.warning("No voice message found in update")
            await update.message.reply_text("لطفاً یک **پیام صوتی** ارسال کنید\\.", parse_mode="MarkdownV2")
            return

        logger.info("Downloading voice file")
        file = await context.bot.get_file(update.message.voice.file_id)
        file_path = f"voices/{uuid.uuid4()}.ogg"
        os.makedirs("voices", exist_ok=True)
        await file.download_to_drive(file_path)
        logger.info(f"Voice file saved to {file_path}")

        async with transcription_lock:
            logger.info("Starting transcription")
            transcript = transcribe_audio(file_path)
            if "error" in transcript.lower():
                logger.error(f"Transcription failed: {transcript}")
                await update.message.reply_text(f"⚠️ خطا در پردازش صوت: {escape_markdown_v2(transcript)}", parse_mode="MarkdownV2")
                os.remove(file_path)
                return
            logger.info(f"Transcription successful: {transcript}")

        logger.info("Starting summarization")
        summary = summarize_text(transcript)
        if "error" in summary.lower():
            logger.error(f"Summarization failed: {summary}")
            await update.message.reply_text(f"⚠️ خطا در خلاصه‌سازی: {escape_markdown_v2(summary)}", parse_mode="MarkdownV2")
            os.remove(file_path)
            return
        logger.info(f"Summarization successful: {summary}")

        logger.info("Saving to database")
        report_id = save_report(user_id, file_path, transcript, summary)
        logger.info(f"Saved report with ID {report_id}")

        # Send summary with MarkdownV2, escaping special characters
        escaped_summary = escape_markdown_v2(summary)
        response = f"**خلاصه گزارش**:\n{escaped_summary}"
        await update.message.reply_text(response, parse_mode="MarkdownV2")
        logger.info(f"Sent summary to user {user_id}")

    except Exception as e:
        logger.error(f"Error in handle_voice: {str(e)}", exc_info=True)
        await update.message.reply_text(f"⚠️ خطا: {escape_markdown_v2(str(e))}", parse_mode="MarkdownV2")
        if os.path.exists(file_path):
            os.remove(file_path)

async def debug_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received update: {update.to_dict()}")  # Log only, no reply

def setup_bot():
    logger.info("Setting up Telegram bot")
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.VOICE, handle_voice))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.VOICE, debug_update))
        logger.info("Bot setup complete")
        return application
    except Exception as e:
        logger.error(f"Failed to setup bot: {str(e)}")
        raise
