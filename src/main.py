import asyncio
import os

from dotenv import load_dotenv
from telegram.ext import Application

from src.bot.bot import start_bot
from src.config.config import BotConfig


def load_config() -> BotConfig:
    # Load configuration from a file or environment variables
    load_dotenv()
    return BotConfig(TOKEN=os.getenv("TELEGRAM_BOT_TOKEN"))

def main():
    config = load_config()
    application = Application.builder().token(config.TOKEN).build()
    application.run_polling()

if __name__ == "__main__":
    main()