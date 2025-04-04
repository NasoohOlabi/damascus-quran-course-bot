import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class BotConfig:
    TOKEN: str
    LOG_LEVEL: str = 'INFO'

    @classmethod
    def from_env(cls) -> 'BotConfig':
        load_dotenv()
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError('TELEGRAM_BOT_TOKEN missing from environment')
        return cls(
            TOKEN=token,
            LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO').upper()
        )
