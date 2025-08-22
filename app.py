import os
import json
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

# =====================
# Logging
# =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================
# Config
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
BLOCKONOMICS_KEY = os.getenv("BLOCKONOMICS_KEY", "")
WELCOME_VIDEO_URL = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"

PORT = int(os.getenv("PORT", 8080))
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")

# =====================
# Handlers
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    welcome_text = (
        "☠️ TTW's Null_Bot ☠️\n"
        f"📢 Welcome {user.first_name}!\n\n"
        "🌐 Crack the code, tax the globe 🌐"
    )

    keyboard = [
        [InlineKeyboardButton("🛒 Shop", callback_data="cat:root")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("💬 Support", callback_data="support")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if WELCOME_VIDEO_URL:
        await update.message.reply_video(
            video=WELCOME_VIDEO_URL,
            caption=welcome_text,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_text(
            text=welcome_text, reply_markup=reply_markup
        )


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📂 Categories coming soon...")


async def item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📦 Item details here.")


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("ℹ️ About TTW: Taxing the World, one exploit at a time.")


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💬 Support: Contact @YourHandle")


async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⬅️ Back to main menu.")


async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💰 Purchase flow coming soon.")


# =====================
# FastAPI Server
# =====================
server = FastAPI()

application = Application.builder().token(BOT_TOKEN).build()

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(category_handler, pattern="^cat:"))
application.add_handler(CallbackQueryHandler(item_handler, pattern="^item:"))
application.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
application.add_handler(CallbackQueryHandler(support_handler, pattern="^support$"))
application.add_handler(CallbackQueryHandler(back_handler, pattern="^back:"))
application.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy:"))

@server.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

@server.get("/")
async def home():
    return {"status": "ok", "message": "Bot is alive"}

@server.on_event("startup")
async def on_startup():
    if RENDER_HOST:
        webhook_url = f"https://{RENDER_HOST}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
    else:
        logger.info("⚠️ Running without webhook (probably local dev).")


# =====================
# Local Run (optional)
# =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:server", host="0.0.0.0", port=PORT, reload=True)