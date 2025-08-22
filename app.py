
import os
import json
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "8306200181:AAHP56BkD6eZOcqjI6MZNrMdU7M06S0tIrs"
BLOCKONOMICS_KEY = "Z3iMV7YBEl9dk6yla6j8YDT3zNvAkho4MyQ27ridgnI"  # Optional for crypto payments
WELCOME_VIDEO_URL = "https://ik.imagekit.io/myrnjevjk/game%20over.mp4?updatedAt=1754980438031"  # Optional welcome video

# =========================
# LEGITIMATE SHOP DATA
# =========================
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

# =========================
# PAYMENT HELPERS
# =========================
async def get_btc_price_usd() -> float:
    """Get current BTC price in USD"""
    url = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    price_str = data["bpi"]["USD"]["rate"].replace(",", "").replace("$", "")
                    return float(price_str)
                else:
                    logger.warning(f"Price API returned status {r.status}")
                    return 50000.0
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
        return 50000.0

async def generate_btc_address() -> str:
    """Generate a new BTC address for payment (requires Blockonomics API)"""
    if not BLOCKONOMICS_KEY:
        # For demo purposes, return a dummy address
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
    """Check if payment has been received (requires Blockonomics API)"""
    if not BLOCKONOMICS_KEY:
        # For demo purposes, simulate payment after 2 minutes
        await asyncio.sleep(120)
        return True
    
    url = f"https://www.blockonomics.co/api/address/{address}"
    headers = {"Authorization": f"Bearer {BLOCKONOMICS_KEY}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status != 200:
                    return False
                data = await r.json()
                received = data.get("received", 0) / 100000000  # Convert satoshi to BTC
                return received >= expected_amount
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
    return False

# =========================
# BOT HANDLERS
# =========================
async def show_main_menu(query=None, update=None):
    """Display the main category menu"""
    keyboard = []
    for key, cat in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(
            f"{cat['emoji']} {key.replace('_', ' ').title()}", 
            callback_data=f"cat:{key}"
        )])
    
    # Add additional options
    keyboard.append([InlineKeyboardButton("ℹ️ About", callback_data="about")])
    keyboard.append([InlineKeyboardButton("📞 Support", callback_data="support")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🛒 *Welcome to TTW'S Null_Bot ☠️*\n\nChoose a category to browse our products:"
    
    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_text = f"👋 Welcome {user.first_name}!\n\n🛒 *TTW'S Null_Bot*\n\nWe offer high-quality digital products to help you tax the world for profit and lulz 🤡"
    
    # Try to send welcome video if URL is provided
    if WELCOME_VIDEO_URL:
        try:
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=WELCOME_VIDEO_URL,
                caption=welcome_text,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Video send failed: {e}")
            await update.message.reply_text(welcome_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, parse_mode="Markdown")

    await show_main_menu(update=update)

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection"""
    query = update.callback_query
    await query.answer()
    cat_key = query.data.split(":")[1]
    category = CATEGORIES[cat_key]

    keyboard = []
    for item_id, item in category["items"].items():
        keyboard.append([InlineKeyboardButton(
            f"{item['emoji']} {item['name']} - ${item['price']}", 
            callback_data=f"item:{cat_key}:{item_id}"
        )])
    keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="back:main")])

    await query.edit_message_text(
        f"{category['emoji']} *{cat_key.replace('_', ' ').title()}*\n\nSelect an item to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def item_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle item selection and show details"""
    query = update.callback_query
    await query.answer()
    _, cat_key, item_id = query.data.split(":")
    item = CATEGORIES[cat_key]["items"][item_id]

    keyboard = [
        [InlineKeyboardButton("💰 Buy Now", callback_data=f"buy:{cat_key}:{item_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"cat:{cat_key}")]
    ]
    
    description = item.get("description", "No description available.")
    
    await query.edit_message_text(
        f"📦 *{item['name']}*\n\n📝 {description}\n\n💵 Price: ${item['price']}\n\nReady to purchase?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle about section"""
    query = update.callback_query
    await query.answer()
    
    about_text = """☠️*TTW's Null_Bot*

🚨 We provide high-quality digital products to help you tax the world for profit and lulz:

🎓 **ScamPages**: The highest quality coded scampages on the darkweb just add tele bot token
🎨 **Tutorials**: Freshly hacked from a major DB hack by @therealdysthemix 
📚 **Data**: Fullz, Profiles, CVV's and other data freshly spammed
🛠️ **Tools**: Spamming, hacking, carding, AI JailBreaks and other kinds of tools

All products are:
✅ Instantly downloadable
✅ High quality and tested
✅ Regularly updated
✅ Backed by support

💳 We accept Bitcoin payments for secure, anonymous transactions."""

    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back:main")]]
    
    await query.edit_message_text(
        about_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support section"""
    query = update.callback_query
    await query.answer()
    
    support_text = """📞 *Customer Support*

Need help? We're here for you!

📧 **Email**: dayglowgiggles@proton.me
💬 **Telegram**: @therealdysthemix
⏰ **Hours**: 9 AM - 12 AM MST

**Common Questions:**
• Products are delivered instantly after payment (1 confirmation needed)
• All sales are final NO EXCEPTIONS
• Limited support offered but don't buy if you don't know how to use
• Bulk discounts available for multiple items

**Payment Issues:**
If you experience payment problems, contact @therealdysthemix with your transaction details."""

    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back:main")]]
    
    await query.edit_message_text(
        support_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back navigation"""
    query = update.callback_query
    await query.answer()
    if query.data == "back:main":
        await show_main_menu(query=query)

async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle purchase initiation"""
    query = update.callback_query
    await query.answer()
    _, cat_key, item_id = query.data.split(":")
    item = CATEGORIES[cat_key]["items"][item_id]

    # Get BTC price and calculate amount
    btc_usd = await get_btc_price_usd()
    amount_btc = round(item["price"] / btc_usd, 8)
    
    # Generate payment address
    address = await generate_btc_address()
    if not address:
        await query.edit_message_text("⚠️ Could not generate payment address. Please try again later.")
        return

    # Store purchase info
    context.user_data["purchase"] = {
        "item": item,
        "address": address,
        "amount": amount_btc,
        "delivered": False
    }

    payment_text = f"""💰 *Payment Details*

📦 **Product**: {item['name']}
💵 **Price**: ${item['price']} USD
₿ **Amount**: {amount_btc} BTC

**Payment Address:**
`{address}`

⚠️ **Important:**
• 🚨 Send EXACTLY {amount_btc} BTC 🚨
• Payment will be verified automatically
• Product delivered instantly after confirmation
• Do not send from an exchange (use personal wallet)

⏱️ Payment expires in 30 minutes"""

    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back:main")]]
    
    await query.edit_message_text(
        payment_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Start payment verification
    asyncio.create_task(verify_payment_loop(update, context))

async def verify_payment_loop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Continuously check for payment confirmation"""
    purchase = context.user_data.get("purchase")
    if not purchase or purchase.get("delivered"):
        return
    
    item = purchase["item"]
    address = purchase["address"]
    amount = purchase["amount"]
    
    # Check for payment for 30 minutes (60 checks, 30 seconds apart)
    for i in range(60):
        if purchase.get("delivered"):  # Check if already delivered
            return
            
        paid = await check_payment(address, amount)
        if paid:
            await deliver_product(update, context, item)
            return
            
        # Send status update every 10 checks (5 minutes)
        if i > 0 and i % 10 == 0:
            remaining_time = 30 - (i * 0.5)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⏳ Still waiting for payment... {remaining_time:.0f} minutes remaining"
            )
        
        await asyncio.sleep(30)
    
    # Payment timeout
    if not purchase.get("delivered"):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Payment timeout. Transaction expired. Please start over if you'd like to purchase."
        )

async def deliver_product(update: Update, context: ContextTypes.DEFAULT_TYPE, item: dict):
    """Deliver the purchased product"""
    purchase = context.user_data.get("purchase", {})
    if purchase.get("delivered"):
        return
    
    file_path = item["file"]
    
    try:
        # Send confirmation message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ *Payment Confirmed!*\n\n📦 Delivering: {item['name']}\n\nThank you for your purchase! 🎉",
            parse_mode="Markdown"
        )
        
        # Send the file
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=file,
                    filename=f"{item['name']}.zip",
                    caption=f"📥 Your purchase: *{item['name']}*\n\nEnjoy your product! For support, use /start and select Support.",
                    parse_mode="Markdown"
                )
        else:
            # File doesn't exist - send download link or alternative
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"📧 Your download link will be sent to you shortly via email.\n\nIf you don't receive it within 10 minutes, please contact support."
            )
        
        # Mark as delivered
        purchase["delivered"] = True
        
        # Send receipt/invoice
        await send_receipt(update, context, item)
        
    except Exception as e:
        logger.error(f"Error delivering product: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ There was an issue delivering your product. Our support team has been notified and will contact you shortly."
        )

async def send_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE, item: dict):
    """Send purchase receipt"""
    user = update.effective_user
    purchase = context.user_data.get("purchase", {})
    
    receipt_text = f"""🧾 *Purchase Receipt*

**Customer**: {user.first_name} {user.last_name or ''}
**Product**: {item['name']}
**Price**: ${item['price']} USD
**Payment**: {purchase.get('amount', 0)} BTC
**Date**: {asyncio.get_event_loop().time()}
**Status**: ✅ Completed

Thank you for choosing Digital Store!
For support: /start → Support"""

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=receipt_text,
        parse_mode="Markdown"
    )

def main():
    """Initialize and run the bot"""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your BOT_TOKEN in the configuration section")
        return
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_handler, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(item_handler, pattern="^item:"))
    app.add_handler(CallbackQueryHandler(about_handler, pattern="^about$"))
    app.add_handler(CallbackQueryHandler(support_handler, pattern="^support$"))
    app.add_handler(CallbackQueryHandler(back_handler, pattern="^back:"))
    app.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy:"))

    logger.info("🤖 Digital Store Bot is running...")
    print("✅ Bot started successfully!")
    print("💡 Make sure to:")
    print("   1. Create a 'files' directory with your digital products")
    print("   2. Set up your Blockonomics API key for real payments")
    print("   3. Add your actual product files")
    
    app.run_polling()

if __name__ == "__main__":
    main()
