import os
from dataclasses import dataclass
from typing import Any, Dict

from dotenv import load_dotenv


@dataclass
class BotConfig:
    """Bot configuration class."""
    TOKEN: str
    GOOGLE_SHEETS_CREDENTIALS: Dict[str, Any]
    DEFAULT_TIMEOUT: float = 30.0
    RECONNECT_DELAY: float = 10.0
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Create config from environment variables."""
        load_dotenv()
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
            
        # Load Google Sheets credentials from environment or file
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        if credentials_path and os.path.exists(credentials_path):
            import json
            with open(credentials_path) as f:
                credentials = json.load(f)
        else:
            raise ValueError("GOOGLE_SHEETS_CREDENTIALS_PATH not found or invalid")
            
        return cls(
            TOKEN=token,
            GOOGLE_SHEETS_CREDENTIALS=credentials
        )
    
    def get_connection_defaults(self) -> Dict[str, Any]:
        """Get default connection settings."""
        return {
            "connect_timeout": self.DEFAULT_TIMEOUT,
            "read_timeout": self.DEFAULT_TIMEOUT,
            "write_timeout": self.DEFAULT_TIMEOUT,
            "tzinfo": None
        }
