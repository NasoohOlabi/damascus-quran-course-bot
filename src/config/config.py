import os
from dataclasses import dataclass
from typing import Any, Dict

from dotenv import load_dotenv


@dataclass
class BotConfig:
    """Bot configuration class."""
    TOKEN: str
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Create config from environment variables."""
        load_dotenv()
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please create a .env file with your bot token.")
        
        return cls(TOKEN=token)
    
    def get_connection_defaults(self) -> Dict[str, Any]:
        """Get default connection settings."""
        return {
            "connect_timeout": self.DEFAULT_TIMEOUT,
            "read_timeout": self.DEFAULT_TIMEOUT,
            "write_timeout": self.DEFAULT_TIMEOUT,
            "tzinfo": None
        }
