#!/usr/bin/env python
import os
import logging
from uuid import uuid4

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from billdb import Bill, db_template

# Replace 'YOUR_BOT_TOKEN' with the token you obtained from BotFather
# Get the value of an environment variable
TOKEN = os.getenv('TOKEN')
PHOTO, FORCE = range(2)
DB_PATH = './bills-{}.db'

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

available_commands = 'Available commands:\n- /newdb - create new db if you dont have one\n- /qr -- for inserting bill from qr\n- /insert -- for custom bill insert\n- /search -- for making a search on db\n - /delete -- to delete bill by its id\n- /getdb - send your db file to you'


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    db_path = DB_PATH.format(user.id)
    await update.message.reply_markdown(
            rf"Hi {user.mention_markdown()}! I will manage your bills with SQLite db." + available_commands,
    )
    if os.path.exists(db_path):
        await update.message.reply_text('You already have the db file.')
    else:
        await update.message.reply_text('To create a db for yourself send /newdb command.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_markdown(available_commands)

async def get_qr_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Geting qr link and insert it to the db"""
    user = update.message.from_user
    link = update.message.text
    await update.message.delete()
    message_working = await update.message.reply_text('Working on your request...')

    Bill.connect_to_sqlite(DB_PATH.format(user.id))
    bill = Bill().from_qr(link)
    bill.insert(force_dup=False)

    if bill.dup_list:
        Bill.close_sqlite()
        reply_keyboard = [["/cancel"], ["/force"]]
        response = 'finded duplicates in db ({})\nyou can use **/force** command\n'.format(len(bill.dup_list))
        dup_example = bill.dup_list[0]
        # ['id', 'name', 'date', 'price', 'currency', 'bill_text']
        response += '{}\nname: {}\ndate: {}\nprice: {} {}\nbill_text:\n{}'.format(str(dup_example[0]), dup_example[1], dup_example[2], str(dup_example[3]), dup_example[4], dup_example[5])
        context.user_data["bill"] = bill
        await message_working.delete()
        await update.message.reply_text(
            response,
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="cancel or force?"
            )
        )
        return FORCE

async def insert_with_force(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inserting bill with force"""
    user = update.message.from_user
    bill = context.user_data.get('bill')
    del context.user_data["bill"]
    if bill is None:
        await update.message.reply_text('Something wrong with qr link. Sowwy (')
        return ConversationHandler.END

    message_working = await update.message.reply_text('Forcefully inserting bill to the db...')

    Bill.connect_to_sqlite(DB_PATH.format(user.id))
    bill.insert(force_dup=True)

    Bill.close_sqlite()
    response = 'FORCE WAS USED\n\n'
    response += '{}\nname: {}\ndate: {}\nprice: {} {} ({})\n{}\nitems: {}\n[link]({})'.format(str(bill.timestamp), bill.name, bill.date, str(bill.price), bill.currency, bill.exchange_rate, bill.country, str(len(bill.items)), bill.link)
    await message_working.delete()
    await update.message.reply_markdown(response)
    return ConversationHandler.END

async def start_custom_insert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Lets add bill.\nTell me the name:')
    return BILL_NAME

async def get_bill_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return BILL_DATE

async def get_bill_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return BILL_PRICE

async def get_bill_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return BILL_CURRENCY

async def get_bill_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return BILL_CURRENCY

async def create_new_db(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    db_path = DB_PATH.format(user.id)
    if os.path.exists(db_path):
        await update.message.reply_text('DB already exists.')
    else:
        Bill.connect_to_sqlite(db_path)
        Bill.cursor.executescript(db_template)
        Bill.close_sqlite()
        await update.message.reply_text('DB successfully created.')
    return

async def get_db_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    db_path = DB_PATH.format(user.id)
    if os.path.exists(db_path):
        await update.message.reply_document(db_path, filename='bills.db')
    else:
        await update.message.reply_text('You dont have a db file.')
    return

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
    application.add_handler(CommandHandler("newdb", create_new_db))
    application.add_handler(CommandHandler("getdb", get_db_file))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    qr_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^https://suf\.purs\.gov\.rs.*'), get_qr_link)],
        states={
            FORCE: [CommandHandler('force', insert_with_force)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(qr_conv)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
