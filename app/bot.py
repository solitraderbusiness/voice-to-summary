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
import time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

transcription_lock = asyncio.Lock()
TELEGRAM_FILE_SIZE_LIMIT = 20 * 1024 * 1024  # 20 MB limit for getFile

def escape_markdown_v2(text):
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r'([_\*\[\]()~`>#+\-=|{}.!\\])'
    return re.sub(special_chars, r'\\\1', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    logger.info(f"Received /start command from user {user_id}")
    await update.message.reply_text("لطفاً یک پیام صوتی یا فایل صوتی ارسال کنید تا آن را خلاصه کنم\\!", parse_mode="MarkdownV2")

async def handle_voice_or_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        logger.info(f"Received message from user {user_id}")

        # Check for voice or audio message
        if update.message.voice:
            audio_obj = update.message.voice
            logger.info("Processing voice message")
        elif update.message.audio:
            audio_obj = update.message.audio
            logger.info("Processing audio message")
        else:
            logger.warning("No voice or audio message found in update")
            await update.message.reply_text("لطفاً یک **پیام صوتی یا فایل صوتی** ارسال کنید\\.", parse_mode="MarkdownV2")
            return

        # Check file size before attempting download
        file_size = audio_obj.file_size
        logger.info(f"Audio file size: {file_size} bytes")
        if file_size > TELEGRAM_FILE_SIZE_LIMIT:
            logger.warning(f"File size {file_size} bytes exceeds Telegram limit of {TELEGRAM_FILE_SIZE_LIMIT} bytes")
            await update.message.reply_text(
                f"⚠️ فایل صوتی بزرگ‌تر از حد مجاز \\(۲۰ مگابایت\\) است\\. لطفاً فایل را به‌صورت دستی دانلود کرده و مجدداً به‌صورت فایل صوتی کوچک‌تر \\(کمتر از ۲۰ مگابایت\\) ارسال کنید\\.",
                parse_mode="MarkdownV2"
            )
            return

        logger.info("Downloading audio file")
        file = await context.bot.get_file(audio_obj.file_id)
        # Determine file extension dynamically
        file_extension = os.path.splitext(file.file_path)[1] if file.file_path else ".ogg"
        if not file_extension:
            file_extension = ".ogg"  # Default to .ogg if unknown
        file_path = f"voices/{uuid.uuid4()}{file_extension}"
        os.makedirs("voices", exist_ok=True)
        try:
            await file.download_to_drive(file_path)
            logger.info(f"Audio file saved to {file_path}, size: {os.path.getsize(file_path)} bytes")
        except Exception as e:
            logger.error(f"Failed to download audio file: {str(e)}")
            await update.message.reply_text(f"⚠️ خطا در دانلود فایل صوتی: {escape_markdown_v2(str(e))}", parse_mode="MarkdownV2")
            return

        start_time = time.time()
        async with transcription_lock:
            logger.info(f"Acquired lock for user {user_id}, waited {time.time() - start_time:.2f} seconds")
            logger.info("Starting transcription")
            transcript = transcribe_audio(file_path)
            if "error" in transcript.lower():
                logger.error(f"Transcription failed: {transcript}")
                await update.message.reply_text(f"⚠️ خطا در پردازش فایل صوتی: {escape_markdown_v2(transcript)}", parse_mode="MarkdownV2")
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

        escaped_summary = escape_markdown_v2(summary)
        response = f"**خلاصه گزارش**:\n{escaped_summary}"
        await update.message.reply_text(response, parse_mode="MarkdownV2")
        logger.info(f"Sent summary to user {user_id}, total time {time.time() - start_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error in handle_voice_or_audio: {str(e)}", exc_info=True)
        await update.message.reply_text(f"⚠️ خطا: {escape_markdown_v2(str(e))}", parse_mode="MarkdownV2")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

async def debug_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received update: {update.to_dict()}")  # Log only, no reply

def setup_bot():
    logger.info("Setting up Telegram bot")
    try:
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        # Handle both voice and audio messages
        application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_or_audio))
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~(filters.VOICE | filters.AUDIO), debug_update))
        logger.info("Bot setup complete")
        return application
    except Exception as e:
        logger.error(f"Failed to setup bot: {str(e)}")
        raise
