from telegram import Bot, ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import telegram
import asyncio
import time
import configparser

# read config
# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file
config.read('./config.ini')

# Access values from the configuration file
BOT_TOKEN = config.get('General', 'BOT_TOKEN')

def send(chatID, message):
    try:
        # Initialisation du bot
        bot = Bot(token=BOT_TOKEN)
        
        try:
            asyncio.run(bot.send_message(chat_id=chatID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2))
        except Exception as e:
            print(f"Error sending message : {e}")
    except:
        pass