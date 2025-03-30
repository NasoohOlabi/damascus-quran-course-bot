import asyncio
from src.bot.bot import start_bot
from src.config.config import BotConfig

def main():
    """Main entry point for the bot."""
    # Load configuration
    config = BotConfig.from_env()
    
    # Run the bot
    asyncio.run(start_bot(config))

if __name__ == '__main__':
    main()