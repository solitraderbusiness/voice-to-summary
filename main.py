import logging
from app.bot import setup_bot
from app.api import app as fastapi_app
import uvicorn
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting application")
    
    # Start Telegram bot
    logger.info("Initializing Telegram bot")
    bot_app = setup_bot()
    await bot_app.initialize()
    logger.info("Starting bot polling")
    await bot_app.start()
    bot_task = asyncio.create_task(bot_app.updater.start_polling(drop_pending_updates=True))
    
    # Start FastAPI
    logger.info("Starting FastAPI server")
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8001)
    server = uvicorn.Server(config)
    fastapi_task = asyncio.create_task(server.serve())
    
    # Wait for both tasks
    await asyncio.gather(bot_task, fastapi_task)
    logger.info("Application shutdown")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Application failed: {str(e)}", exc_info=True)
