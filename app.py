import os
import logging
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# Logging
# =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================
# Config
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs")
BLOCKONOMICS_KEY = os.getenv("BLOCKONOMICS_KEY", "Z3iMV7YBEl9dk6yla6j8YDT3zNvAkho4MyQ27ridgnI")
WELCOME_VIDEO_URL = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"

PORT = int(os.getenv("PORT", 8080))
RENDER_HOST = os.getenv("https://basic-bot-1q9e.onrender.com")

# =====================
# SHOP DATA
# =====================
CATEGORIES = {
    "tutorials": {
        "emoji": "💻",
        "items": {
            "web_dev": {
                "name": "Complete Web Development Course",
                "price": 49,
                "emoji": "💾",
                "file": "files/web_dev_course.zip",
                "description": "Learn HTML, CSS, JavaScript, and React from scratch"
            },
            "python_basics": {
                "name": "Python Programming Fundamentals",
                "price": 39,
                "emoji": "💵",
                "file": "files/python_course.zip",
                "description": "Master Python programming with hands-on projects"
            },
        },
    },
    "scampages": {
        "emoji": "🎨",
        "items": {
            "website_templates": {
                "name": "Professional Website Templates Pack",
                "price": 25,
                "emoji": "🌐",
                "file": "files/website_templates.zip",
                "description": "10 responsive website templates for businesses"
            },
            "resume_templates": {
                "name": "Modern Resume Templates",
                "price": 15,
                "emoji": "📄",
                "file": "files/resume_templates.zip",
                "description": "Professional resume templates in various formats"
            },
        },
    },
    "data": {
        "emoji": "📖",
        "items": {
            "business_guide": {
                "name": "Complete Business Startup Guide",
                "price": 20,
                "emoji": "🚀",
                "file": "files/business_guide.pdf",
                "description": "Step-by-step guide to starting your own business"
            },
            "marketing_book": {
                "name": "Digital Marketing Mastery",
                "price": 18,
                "emoji": "📈",
                "file": "files/marketing_book.pdf",
                "description": "Learn effective digital marketing strategies"
            },
        },
    },
    "tools": {
        "emoji": "🛠️",
        "items": {
            "productivity_apps": {
                "name": "Productivity Apps Bundle",
                "price": 35,
                "emoji": "⚡",
                "file": "files/productivity_apps.zip",
                "description": "Collection of useful productivity applications"
            },
            "design_assets": {
                "name": "Design Assets Pack",
                "price": 30,
                "emoji": "🖱️",
                "file": "files/design_assets.zip",
                "description": "Icons, fonts, and graphics for designers"
            },
        },
    },
}

# =====================
# Payment Helpers
# =====================
async def get_btc_price_usd() -> float:
    url = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    price_str = data["bpi"]["USD"]["rate"].replace(",", "").replace("$", "")
                    return float(price_str)
                return 50000.0
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
        return 50000.0

async def generate_btc_address() -> str:
    if not BLOCKONOMICS_KEY:
        return "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
    url = "https://www.blockonomics.co/api/new_address"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as r:
                data = await r.json()
                return data.get("address")
    except Exception as e:
        logger.error(f"Error generating BTC address: {e}")
        return None

async def check_payment(address: str, expected_amount: float) -> bool:
    if not BLOCKONOMICS_KEY:
        await asyncio.sleep(5)
        return True
    url = f"https://www.blockonomics.co/api/address/{address}"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status != 200:
                    return False
                data = await r.json()
                received = data.get("received", 0) / 100000000
                return received >= expected_amount
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        return False

# =====================
# Bot Handlers
# =====================
async def show_main_menu(query=None, update=None):
    keyboard = []
    for key, cat in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(f"{cat['emoji']} {key.replace('_',' ').title()}", callback_data=f"cat:{key}")])
    keyboard.append([InlineKeyboardButton("ℹ️ About", callback_data="about")])
    keyboard.append([InlineKeyboardButton("📞 Support", callback_data="support")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = " *☠️ Null_Bot ☠️*\n\nChoose a category to browse our products:"
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

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

@server.on_event("startup")
async def on_startup():
    if RENDER_HOST:
        webhook_url = f"https://{RENDER_HOST}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set: {webhook_url}")
    else:
        logger.info("⚠️ Running locally without webhook.")

# =====================
# Optional Local Run
# =====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:server", host="0.0.0.0", port=PORT, reload=True)