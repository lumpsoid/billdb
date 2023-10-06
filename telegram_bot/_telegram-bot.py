#!/usr/bin/env python
import os
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Replace 'YOUR_BOT_TOKEN' with the token you obtained from BotFather
# Get the value of an environment variable
TOKEN = os.getenv('BOT_TOKEN')
PHOTO, LINK = range(2)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

available_commands = 'Available commands:\n- /qr -- for inserting bill from qr\n- /insert -- for custom bill insert\n- /search -- for making a search on db\n - /delete -- to delete bill by its id'


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
            rf"Hi {user.mention_html()}!\nI will manage your bills with SQLite db. We can create it or start from file.\n" + available_commands,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(available_commands)

async def start_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a process of inserting a bill from provided qr."""
    user = update.message.from_user
    await update.message.reply_text(
            'Send me a qr link to a bill!'
    )
    return LINK

async def get_qr_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a process of inserting a bill from provided qr."""
    user = update.message.from_user
    await update.message.reply_text(available_commands)
    return ConversationHandler.END

async def start_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a process of inserting a bill from provided qr."""
    user = update.message.from_user
    await update.message.reply_text('Send me a dickpick')
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a process of inserting a bill from provided qr."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive("user_photo.jpg")
    logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")
    await update.message.reply_text('Get it.')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a process of inserting a bill from provided qr."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO

    qr_conv = ConversationHandler(
        entry_points=[CommandHandler("qr", start_qr)],
        states={
            LINK: [MessageHandler(filters.Regex("^(http*)$"), get_qr_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(qr_conv)

    photo_conv = ConversationHandler(
        entry_points=[CommandHandler("photo", start_photo)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(photo_conv)


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
