import os
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# Logging
# =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================
# Config
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BLOCKONOMICS_KEY = os.getenv("BLOCKONOMICS_KEY", "")
WELCOME_VIDEO_URL = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"

PORT = int(os.getenv("PORT", 8080))
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")  # your Render hostname

# =====================
# Shop Data (simplified)
# =====================
CATEGORIES = {
    "tutorials": {"emoji": "💻", "items": {}},
    "scampages": {"emoji": "🎨", "items": {}},
    "data": {"emoji": "📖", "items": {}},
    "tools": {"emoji": "🛠️", "items": {}},
}

# =====================
# Bot Handlers
# =====================
async def show_main_menu(query=None, update=None):
    keyboard = []
    for key, cat in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(f"{cat['emoji']} {key.title()}", callback_data=f"cat:{key}")])
    keyboard.append([InlineKeyboardButton("ℹ️ About", callback_data="about")])
    keyboard.append([InlineKeyboardButton("📞 Support", callback_data="support")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "*☠️ Null_Bot ☠️*\n\nChoose a category:"
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        "☠️ TTW's Null_Bot ☠️\n"
        f"📢 Welcome {user.first_name}!\n\n"
        "🌐 Crack the code, tax the globe 🌐"
    )
    await show_main_menu(update=update)
    await update.message.reply_text(text=welcome_text, parse_mode="Markdown")

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
    await query.edit_message_text("💬 Support: Contact @therealdysthemix")

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_main_menu(query=query)

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💰 Purchase flow coming soon.")

# =====================
# FastAPI Server + Webhook
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

async def reset_webhook():
    bot = Bot(BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    if RENDER_HOST:
        url = f"https://{RENDER_HOST}/webhook"
        await bot.set_webhook(url)
        logger.info(f"✅ Webhook set to: {url}")
    else:
        logger.info("⚠️ Running locally without webhook.")

@server.on_event("startup")
async def on_startup():
    await reset_webhook()

# =====================
# Optional Local Run
# =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:server", host="0.0.0.0", port=PORT, reload=True)