import os
import json
import asyncio
import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, ApplicationBuilder
import aiohttp

# =========================
# CONFIG
BOT_TOKEN = os.getenv("8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs")
BLOCKONOMICS_API_KEY = os.getenv("upSaWm3RiAS60lWT8One1HCIiprfDnJADadJE8z3e0c")
VIDEO_PATH = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"
ADDRESS_FILE = "btc_addresses.json"
PORT = 10000
RETRIES = 3
RETRY_DELAY = 2
# =========================

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ensure JSON storage exists
if not os.path.exists(ADDRESS_FILE):
    with open(ADDRESS_FILE, "w") as f:
        json.dump([], f)

# --- BTC generator ---
async def generate_btc_address():
    """Generate BTC address using Blockonomics API."""
    url = "https://www.blockonomics.co/api/new_address"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("address")
                else:
                    logger.warning(f"BTC API returned status {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"BTC generation failed: {e}")
        return None

async def get_btc_address_with_retry(retries=RETRIES, delay=RETRY_DELAY):
    for attempt in range(1, retries + 1):
        addr = await generate_btc_address()
        if addr:
            return addr
        logger.info(f"Retry {attempt}/{retries} failed, waiting {delay}s...")
        await asyncio.sleep(delay)
    return None

def store_btc_address(address, user_id):
    """Store generated BTC addresses for tracking."""
    with open(ADDRESS_FILE, "r+") as f:
        data = json.load(f)
        data.append({"user_id": user_id, "address": address})
        f.seek(0)
        json.dump(data, f, indent=4)

# --- Command handler ---
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("⏳ Generating BTC address...")

    btc_address = await get_btc_address_with_retry()
    if not btc_address:
        await update.message.reply_text("⚠️ Error generating BTC address. Try again later.")
        return

    store_btc_address(btc_address, user_id)

    if os.path.exists(VIDEO_PATH):
        await update.message.reply_video(
            InputFile(VIDEO_PATH),
            caption=f"✅ Your BTC address: `{btc_address}`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"✅ Your BTC address: `{btc_address}`\n⚠️ Video not found. Skipping .mp4.",
            parse_mode="Markdown",
        )

# --- Main ---
async def main():
    if not BOT_TOKEN or not BLOCKONOMICS_API_KEY:
        logger.error("BOT_TOKEN or BLOCKONOMICS_API_KEY environment variables not set!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("test", test_command))

    logger.info(f"Production bot starting on port {PORT}...")
    
    # Use run_polling for simplicity (Render can expose this port)
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
