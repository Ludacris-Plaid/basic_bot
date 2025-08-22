import os
import asyncio
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs")
BLOCKONOMICS_API_KEY = os.getenv("BLOCKONOMICS_API_KEY", "upSaWm3RiAS60lWT8One1HCIiprfDnJADadJE8z3e0c")
WELCOME_VIDEO_URL = os.getenv(
    "WELCOME_VIDEO_URL",
    "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"
)
WEBHOOK_URL = f"https://basic-bot-1q9e.onrender.com/webhook/{BOT_TOKEN}"
PORT = int(os.environ.get("PORT", 10000))
SANDBOX_MODE = not bool(BLOCKONOMICS_API_KEY)

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# SHOP DATA
# =========================
CATEGORIES = {
    "pages": {
        "emoji": "📚",
        "items": {
            "fb_clone": {"name": "Facebook Clone Page", "price": 25, "emoji": "🌐", "file": "files/fb_clone.zip"},
            "insta_clone": {"name": "Instagram Clone Page", "price": 20, "emoji": "📸", "file": "files/insta_clone.zip"},
        },
    },
    "tutorials": {
        "emoji": "📖",
        "items": {
            "phishing_guide": {"name": "Phishing Guide PDF", "price": 15, "emoji": "📝", "file": "files/phishing_guide.pdf"},
            "spam_setup": {"name": "Spam Setup Tutorial", "price": 30, "emoji": "⚡", "file": "files/spam_setup.pdf"},
        },
    },
    "data": {
        "emoji": "📊",
        "items": {
            "email_list": {"name": "Email List 10k", "price": 40, "emoji": "📧", "file": "files/email_list.csv"},
            "combo_list": {"name": "Combo List 50k", "price": 60, "emoji": "💾", "file": "files/combo_list.csv"},
        },
    },
    "other": {
        "emoji": "🎁",
        "items": {
            "vpn": {"name": "Premium VPN Config", "price": 10, "emoji": "🔒", "file": "files/vpn_config.zip"},
            "tools_pack": {"name": "Hacker Tools Pack", "price": 50, "emoji": "🛠️", "file": "files/tools_pack.zip"},
        },
    },
}

# =========================
# BTC HELPERS
# =========================
import aiohttp

async def get_btc_price_usd() -> float:
    if SANDBOX_MODE:
        return 50000.0
    url = "https://www.blockonomics.co/api/price?currency=USD"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as r:
                if r.status == 200:
                    data = await r.json()
                    return float(data.get("price", 50000.0))
    except Exception as e:
        logger.error("Error fetching BTC price: %s", e)
    return 50000.0

async def generate_btc_address() -> str:
    if SANDBOX_MODE:
        return "TEST-BTC-ADDRESS-DO-NOT-SEND"
    url = "https://www.blockonomics.co/api/new_address"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, timeout=20) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("address")
    except Exception as e:
        logger.error("Error generating BTC address: %s", e)
    return None

async def check_payment(address: str) -> bool:
    if SANDBOX_MODE:
        await asyncio.sleep(5)
        return True
    url = f"https://www.blockonomics.co/api/searchhistory?addr={address}"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as r:
                if r.status == 200:
                    data = await r.json()
                    for tx in data.get("history", []):
                        if tx.get("status") == 2:
                            return True
    except Exception as e:
        logger.error("Error checking payment: %s", e)
    return False

# =========================
# TELEGRAM HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if WELCOME_VIDEO_URL:
        await update.message.reply_video(WELCOME_VIDEO_URL, caption="💀 Welcome to *TTW's Null_Bot* 💀", parse_mode="Markdown")
    else:
        await update.message.reply_text("💀 Welcome to TTW's Null_Bot 💀")
    await show_main_menu(update=update)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start to begin.")

async def show_main_menu(update=None, query=None):
    keyboard = [[InlineKeyboardButton(f"{cat['emoji']} {key.capitalize()}", callback_data=f"cat:{key}")]
                for key, cat in CATEGORIES.items()]
    markup = InlineKeyboardMarkup(keyboard)
    text = "🛒 *Main Menu*:\nChoose a category:"
    if query:
        await query.edit_message_text(text=text, reply_markup=markup, parse_mode="Markdown")
    elif update:
        await update.message.reply_text(text=text, reply_markup=markup, parse_mode="Markdown")

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.split(":")[1]
    category = CATEGORIES[cat_key]
    keyboard = [[InlineKeyboardButton(f"{item['emoji']} {item['name']} - ${item['price']}", callback_data=f"item:{cat_key}:{item_id}")]
                for item_id, item in category["items"].items()]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back:main")])
    await query.edit_message_text(f"{category['emoji']} *{cat_key.capitalize()}*:\n\nSelect an item:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, cat_key, item_id = query.data.split(":")
    item = CATEGORIES[cat_key]["items"][item_id]
    keyboard = [
        [InlineKeyboardButton("💰 Buy Now", callback_data=f"buy:{cat_key}:{item_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"cat:{cat_key}")]
    ]
    await query.edit_message_text(f"📦 *{item['name']}*\n💵 Price: ${item['price']}\n\nReady to checkout?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back:main":
        await show_main_menu(query=query)

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, cat_key, item_id = query.data.split(":")
    item = CATEGORIES[cat_key]["items"][item_id]
    btc_usd = await get_btc_price_usd()
    amount_btc = round(item["price"] / btc_usd, 8)
    address = await generate_btc_address()
    if not address:
        await query.edit_message_text("⚠ Could not generate BTC address. Try again later.")
        return
    context.user_data["purchase"] = {"item": item, "address": address, "amount": amount_btc, "delivered": False}
    await query.edit_message_text(f"💀 *{item['name']}*\n💵 Price: ${item['price']}\n₿ Send exactly: *{amount_btc} BTC*\n➡ To Address: `{address}`\n\nPayment will be verified automatically!", parse_mode="Markdown")
    asyncio.create_task(auto_verify_payment(update, context))

async def auto_verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    purchase = context.user_data.get("purchase")
    if not purchase or purchase.get("delivered"):
        return
    item = purchase["item"]
    address = purchase["address"]
    for _ in range(60):
        paid = await check_payment(address)
        if paid:
            file_path = item["file"]
            if os.path.exists(file_path):
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Payment confirmed! Delivering *{item['name']}*...", parse_mode="Markdown")
                await context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(file_path))
                purchase["delivered"] = True
                return
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠ File missing on server.")
                return
        await asyncio.sleep(30)
    if not purchase.get("delivered"):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Payment not found. Please try again later.")

# =========================
# RUN WEBHOOK SERVER
# =========================
async def main():
    application = Application.builder().token(BOT_TOKEN).build()
    # Telegram handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(category_handler, pattern="^cat:"))
    application.add_handler(CallbackQueryHandler(item_handler, pattern="^item:"))
    application.add_handler(CallbackQueryHandler(back_handler, pattern="^back:"))
    application.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy:"))

    # Aiohttp web app
    web_app = web.Application()
    # Health check
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

    # Set webhook
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook set to %s", WEBHOOK_URL)

    # Start aiohttp server
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Webhook server running on port {PORT}")

    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
