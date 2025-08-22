import os
import json
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BLOCKONOMICS_KEY = os.environ.get("BLOCKONOMICS_KEY")
VIDEO_URL = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"

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
async def get_btc_price_usd() -> float:
    url = "https://www.blockonomics.co/api/price?currency=USD"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status == 200:
                    data = await r.json()
                    return float(data.get("price", 50000.0))
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
    return 50000.0

async def generate_btc_address() -> str:
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

async def check_payment(address: str) -> bool:
    url = f"https://www.blockonomics.co/api/searchhistory?addr={address}"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as r:
                if r.status != 200:
                    return False
                data = await r.json()
                for tx in data.get("history", []):
                    if tx.get("status") == 2:
                        return True
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
    return False

# =========================
# MENU HELPERS
# =========================
async def show_main_menu(query=None, update=None):
    keyboard = []
    for key, cat in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(f"{cat['emoji']} {key.capitalize()}", callback_data=f"cat:{key}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🛒 *Main Menu*:\nChoose a category:"
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# =========================
# BOT HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=VIDEO_URL,
            caption="💀 Welcome to *TTW's Null_Bot* 💀\nChoose a category below:",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Video send failed: {e}")
        await update.message.reply_text("💀 Welcome to TTW's Null_Bot 💀")
    await show_main_menu(update=update)

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.split(":")[1]
    category = CATEGORIES[cat_key]

    keyboard = []
    for item_id, item in category["items"].items():
        keyboard.append([InlineKeyboardButton(f"{item['emoji']} {item['name']} - ${item['price']}", callback_data=f"item:{cat_key}:{item_id}")])
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
    await query.edit_message_text(
        f"📦 *{item['name']}*\n💵 Price: ${item['price']}\n\nReady to checkout?",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

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
    await query.edit_message_text(
        f"💀 *{item['name']}*\n💵 Price: ${item['price']}\n₿ Send exactly: *{amount_btc} BTC*\n➡ To Address: `{address}`\n\nPayment will be verified automatically!",
        parse_mode="Markdown"
    )
    asyncio.create_task(auto_verify_payment(update, context))

async def auto_verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    purchase = context.user_data.get("purchase")
    if not purchase or purchase.get("delivered"):
        return
    item = purchase["item"]
    address = purchase["address"]
    while not purchase.get("delivered"):
        if await check_payment(address):
            await update.effective_chat.send_document(document=InputFile(item["file"]), caption=f"✅ Payment received! Here is your {item['name']}")
            purchase["delivered"] = True
            break
        await asyncio.sleep(30)

# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_handler, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(item_handler, pattern="^item:"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back:"))
    app.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy:"))

    logger.info("🤖 TTW's Null_Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
