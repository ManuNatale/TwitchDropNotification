from telegram import Bot, ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import telegram
import asyncio
import threading
import time
import configparser

import firebase_admin
from firebase_admin import db
from flask import Flask, render_template, request

# read config
# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config.ini')

# Access values from the configuration file
databaseURL = config.get('General', 'databaseURL')
firebaseCredFile = config.get('General', 'firebaseCredFile')
BOT_TOKEN = config.get('General', 'BOT_TOKEN')

helpText=f"/start to get your ID\n/edit to change games\n/unsubscribe to unsubscribe "

cred_obj = firebase_admin.credentials.Certificate(firebaseCredFile)
default_app = firebase_admin.initialize_app(cred_obj, {
    'databaseURL':databaseURL
    })

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /start is issued."""
    user = update.effective_user
    #await update.message.reply_html(rf"Hi {user.mention_html()}!",reply_markup=ForceReply(selective=True),)
    await update.message.reply_text(f"Hi,\nYour ID is: `{update.message.chat_id}`", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /help is issued."""
    await update.message.reply_text(helpText)
    
async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    userID=""
    usersDbRefGet = db.reference("/users/").get()
    for user in usersDbRefGet:
        print(user)
        print(usersDbRefGet[user].get("telegram"))
        print(str(update.message.chat_id))
        # check if the telegram user to unsubscribe is the same as the chat id
        if usersDbRefGet[user].get("telegram") == str(update.message.chat_id):
            userID=user
            await update.message.reply_text(f"Click to <a href='twitchdropnotif.pythonanywhere.com/unsubscribe?id={userID}'>unsubscribe</a>", parse_mode=telegram.constants.ParseMode.HTML)
            break

    if userID=="":
        """Send a message when the command /unsubscribe is issued."""
        await update.message.reply_text("You are not subscribed")
        
async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    userID=""
    usersDbRefGet = db.reference("/users/").get()
    for user in usersDbRefGet:
        #print(user)
        #print(usersDbRefGet[user].get("telegram"))
        #print(str(update.message.chat_id))
        # check if the telegram user to unsubscribe is the same as the chat id
        if usersDbRefGet[user].get("telegram") == str(update.message.chat_id):
            userID=user
            await update.message.reply_text(f"Edit your games <a href='twitchdropnotif.pythonanywhere.com/?id={userID}'>HERE</a>", parse_mode=telegram.constants.ParseMode.HTML)
            break

    if userID=="":
        """Send a message when the command /edit is issued."""
        await update.message.reply_text("You are not subscribed")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Echo the user message."""
    #await update.message.reply_text(update.message.text)
    await update.message.reply_text(helpText)

def main(o) -> None:

    """Start the bot."""
    # Create the Application and pass it your bot's token.
    global application
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("edit", edit_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    print("Telegram started listening...")
    asyncio.run(application.run_polling(allowed_updates=Update.ALL_TYPES))


if __name__ == "__main__":
    main(1)

