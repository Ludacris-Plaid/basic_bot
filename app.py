import os
import asyncio
import logging
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs")
BLOCKONOMICS_API_KEY = os.getenv("BLOCKONOMICS_API_KEY", "upSaWm3RiAS60lWT8One1HCIiprfDnJADadJE8z3e0c")
WELCOME_VIDEO_URL = os.getenv("WELCOME_VIDEO_URL", "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031")
WEBHOOK_URL = f"https://basic-bot-1q9e.onrender.com/webhook/{BOT_TOKEN}"

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# TELEGRAM HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome video and message on /start"""
    if WELCOME_VIDEO_URL:
        await update.message.reply_video(WELCOME_VIDEO_URL, caption="👾 Welcome to the bot! 👾")
    else:
        await update.message.reply_text("👾 Welcome to the bot! 👾")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Basic help command"""
    await update.message.reply_text("This is a demo bot running on Render.\nUse /start to begin.")

# =========================
# MAIN APP
# =========================
async def main() -> None:
    # Create Telegram app
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))

    # Create aiohttp app
    web_app = web.Application()

    # Health check endpoint for Render
    async def health(request):
        return web.Response(text="OK")
    web_app.router.add_get("/", health)

    # Webhook endpoint
    async def telegram_webhook(request):
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return web.Response(text="ok")
    web_app.router.add_post(f"/webhook/{BOT_TOKEN}", telegram_webhook)

    # Start Telegram + webhook
    async with application:
        await application.bot.set_webhook(WEBHOOK_URL)
        port = int(os.environ.get("PORT", 10000))
        logger.info(f"Starting webhook server on port {port}...")
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        await application.start()
        await application.updater.start_polling()  # safety fallback
        await application.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
