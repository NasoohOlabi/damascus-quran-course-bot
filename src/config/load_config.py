from src.config.config import BotConfig


def load_config() -> BotConfig:
    return BotConfig.from_env()
