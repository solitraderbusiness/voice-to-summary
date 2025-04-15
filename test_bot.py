import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start from user {update.message.from_user.id}")
    await update.message.reply_text("Hello! I’m a test bot.")

async def debug_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received update: {update.to_dict()}")
    await update.message.reply_text("Debug: Update received.")

async def main():
    logger.info("Starting test bot")
    application = Application.builder().token("7334038211:AAE2SwSd23MqS9JDbczNiG2OhpiH7fo9SW8").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, debug_update))
    await application.initialize()
    logger.info("Starting polling")
    await application.start()
    await application.updater.start_polling()
    logger.info("Polling started")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Test bot failed: {str(e)}", exc_info=True)
