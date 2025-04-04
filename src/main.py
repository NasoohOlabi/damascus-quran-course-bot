import asyncio
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

from bot.bot import handle_menu_choice, handle_start
from src.config.config import BotConfig
from src.utils.logger import setup_logger

# Initialize logger
log = setup_logger('Main', 'INFO')

def load_config() -> BotConfig:
    load_dotenv()
    return BotConfig.from_env()

def main():
    log.info('Initializing bot application')
    config = load_config()
    
    application = Application.builder().token(config.TOKEN).build()
    
    # Register all command handlers
    handlers = [
        CommandHandler('start', handle_start),
        # handle_menu_choice
        CommandHandler('menu', handle_menu_choice),
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    application.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log.warning('Shutdown requested via keyboard interrupt')
    except Exception as e:
        log.critical(f'Fatal error: {str(e)}', exc_info=True)
        raise