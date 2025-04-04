import asyncio
from src.config.config import BotConfig
from src.bot.bot import start_bot

def main():
    config = BotConfig.from_env()
    try:
        asyncio.run(start_bot(config))
    except Exception as e:
        raise

if __name__ == "__main__":
    main()