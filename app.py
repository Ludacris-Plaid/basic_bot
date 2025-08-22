import os
import asyncio
import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
import aiohttp

# =========================
# CONFIG - replace with your real credentials
BOT_TOKEN = "8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs"       # <-- Put your Telegram bot token here
BLOCKONOMICS_API_KEY = "upSaWm3RiAS60lWT8One1HCIiprfDnJADadJE8z3e0c"  # <-- Put your Blockonomics API key here
VIDEO_PATH = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"                     # Optional video file
# =========================

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- BTC generator ---
async def generate_btc_address():
    """
    Generate BTC address using Blockonomics API.
    Returns address string or None on failure.
    """
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

async def get_btc_address_with_retry(retries=3, delay=2):
    for attempt in range(1, retries + 1):
        addr = await generate_btc_address()
        if addr:
            return addr
        logger.info(f"Retry {attempt}/{retries} failed, waiting {delay}s...")
        await asyncio.sleep(delay)
    return None

# --- Command handler ---
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Generating BTC address...")

    btc_address = await get_btc_address_with_retry()
    if not btc_address:
        await update.message.reply_text("⚠️ Error generating BTC address. Try again later.")
        return

    # Check for optional .mp4
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
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or BLOCKONOMICS_API_KEY == "YOUR_BLOCKONOMICS_API_KEY":
        logger.error("Please set your BOT_TOKEN and BLOCKONOMICS_API_KEY in the script!")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("test", test_command))

    logger.info("Production bot starting...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
