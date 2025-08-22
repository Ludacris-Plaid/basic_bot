import os
import json
import logging
import aiohttp
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# CONFIG
BOT_TOKEN = "8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs"
BLOCKONOMICS_API_KEY = "upSaWm3RiAS60lWT8One1HCIiprfDnJADadJE8z3e0c"
VIDEO_URL = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"
ADDRESS_FILE = "btc_addresses.json"
PORT = int(os.getenv("PORT", 10000))
RETRIES = 3
RETRY_DELAY = 2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure BTC storage exists
if not os.path.exists(ADDRESS_FILE):
    with open(ADDRESS_FILE, "w") as f:
        json.dump([], f)

# BTC generation
async def generate_btc_address():
    url = "https://www.blockonomics.co/api/new_address"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_API_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("address")
                logger.warning(f"BTC API returned status {resp.status}")
    except Exception as e:
        logger.error(f"BTC generation failed: {e}")
    return None

async def get_btc_address_with_retry():
    for attempt in range(1, RETRIES + 1):
        addr = await generate_btc_address()
        if addr:
            return addr
        logger.info(f"Retry {attempt}/{RETRIES} failed, waiting {RETRY_DELAY}s...")
        await asyncio.sleep(RETRY_DELAY)
    return None

def store_btc_address(address, user_id):
    with open(ADDRESS_FILE, "r+") as f:
        data = json.load(f)
        data.append({"user_id": user_id, "address": address})
        f.seek(0)
        json.dump(data, f, indent=4)

# Telegram command
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("⏳ Generating BTC address...")

    btc_address = await get_btc_address_with_retry()
    if not btc_address:
        await update.message.reply_text("⚠️ Error generating BTC address. Try again later.")
        return

    store_btc_address(btc_address, user_id)

    # Stream remote video
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(VIDEO_URL) as resp:
                if resp.status == 200:
                    video_stream = BytesIO()
                    async for chunk in resp.content.iter_chunked(1024):
                        video_stream.write(chunk)
                    video_stream.seek(0)
                    await update.message.reply_video(
                        video=video_stream,
                        caption=f"✅ Your BTC address: `{btc_address}`",
                        parse_mode="Markdown"
                    )
                    return
                else:
                    logger.warning(f"Video URL returned status {resp.status}")
    except Exception as e:
        logger.error(f"Failed to fetch video: {e}")

    await update.message.reply_text(
        f"✅ Your BTC address: `{btc_address}`\n⚠️ Could not load video.",
        parse_mode="Markdown"
    )

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("test", test_command))

    # Run webhook (Render-ready)
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,  # <-- corrected
        webhook_url=f"https://YOUR_RENDER_APP_NAME.onrender.com/{BOT_TOKEN}"
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())