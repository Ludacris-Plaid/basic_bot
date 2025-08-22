import os
import json
import logging
import aiohttp
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ===============================
# Load ENV
# ===============================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
BLOCKONOMICS_API_KEY = os.getenv("BLOCKONOMICS_API_KEY", "YOUR_BLOCKONOMICS_API_KEY")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===============================
# Mock Items by Category
# ===============================
CATEGORIES = {
    "pages": [
        {"name": "Landing Page Template", "price": 0.0001},
        {"name": "Portfolio Template", "price": 0.0002},
    ],
    "tutorials": [
        {"name": "Python for Hackers", "price": 0.00015},
        {"name": "Telegram Bot Mastery", "price": 0.00025},
    ],
    "data": [
        {"name": "Sample Leads DB", "price": 0.0003},
        {"name": "SEO Keywords Pack", "price": 0.00035},
    ],
    "other": [
        {"name": "Ebook: Null Tactics", "price": 0.0004},
        {"name": "Exclusive Wallpaper Pack", "price": 0.00005},
    ],
}

# Track purchases
PURCHASES = {}

# ===============================
# Blockonomics: Generate Address
# ===============================
async def get_new_address() -> str:
    url = "https://www.blockonomics.co/api/new_address"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as r:
            if r.status != 200:
                text = await r.text()
                logger.error(f"Error generating BTC address: {text}")
                return None
            data = await r.json()
            return data.get("address")

# ===============================
# Blockonomics: Verify Payment
# ===============================
async def check_payment(address: str) -> bool:
    url = "https://www.blockonomics.co/api/searchhistory"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}
    payload = {"addr": address}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as r:
            if r.status != 200:
                logger.error(f"Blockonomics error {r.status}: {await r.text()}")
                return False

            data = await r.json()
            history = data.get("history", [])

            for tx in history:
                if tx.get("status", 0) >= 1:  # 1+ confirmation
                    return True
    return False

# ===============================
# Bot Handlers
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 Pages", callback_data="cat_pages")],
        [InlineKeyboardButton("📚 Tutorials", callback_data="cat_tutorials")],
        [InlineKeyboardButton("📊 Data", callback_data="cat_data")],
        [InlineKeyboardButton("✨ Other", callback_data="cat_other")],
    ]
    await update.message.reply_text(
        "🤖 Welcome to *TTW's Null_Bot*!\n\nChoose a category:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat_key = query.data.replace("cat_", "")
    items = CATEGORIES.get(cat_key, [])
    keyboard = []

    for i, item in enumerate(items):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} 💰 {item['price']} BTC",
            callback_data=f"buy_{cat_key}_{i}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])

    await query.edit_message_text(
        f"📂 Category: *{cat_key.title()}*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def buy_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, cat, idx = query.data.split("_")
    item = CATEGORIES[cat][int(idx)]

    btc_address = await get_new_address()
    if not btc_address:
        await query.edit_message_text("❌ Error generating BTC address. Try again later.")
        return

    PURCHASES[btc_address] = item

    text = (
        f"🛒 *{item['name']}*\n"
        f"💰 Price: `{item['price']} BTC`\n\n"
        f"⚠️ *Sandbox Mode Active — use testnet coins to pay*\n\n"
        f"➡️ Send *exactly* `{item['price']} BTC` to:\n`{btc_address}`\n\n"
        "Once payment is detected, you’ll get your download link."
    )

    keyboard = [[InlineKeyboardButton("✅ Check Payment", callback_data=f"verify_{btc_address}")]]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"cat_{cat}")])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, address = query.data.split("_", 1)
    paid = await check_payment(address)

    if paid:
        item = PURCHASES.get(address)
        await query.edit_message_text(
            f"✅ Payment confirmed!\n\nHere’s your item: *{item['name']}*\n\n"
            f"📥 [Download Here](https://example.com/{item['name'].replace(' ', '_')})",
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            "❌ Payment not found yet. Please wait a few minutes and try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"verify_{address}")]
            ]),
        )

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

# ===============================
# Main
# ===============================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(buy_item, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(verify_payment, pattern="^verify_"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back_main$"))

    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
