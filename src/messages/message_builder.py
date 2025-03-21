from typing import Any, Dict, List, Optional, Union

from telegram import InlineKeyboardMarkup, InputFile, ParseMode


class MessageBuilder:
    """Builder class for creating formatted messages."""
    
    @staticmethod
    def build_welcome_message(user_first_name: str, keyboard: Optional[InlineKeyboardMarkup] = None) -> Dict[str, Any]:
        """Build welcome message."""
        return {
            'text': (
                f'Hi {user_first_name}! Welcome to the Makin Damascus bot.\n\n'
                'Please select a sheet to work with or create a new one:'
            ),
            'reply_markup': keyboard,
            'parse_mode': ParseMode.MARKDOWN
        }
    
    @staticmethod
    def build_help_message() -> Dict[str, Any]:
        """Build help message."""
        return {
            'text': (
                'Send me data in this format:\n'
                '```\n'
                'field1: value1\n'
                'field2: value2\n'
                'field3: value3\n'
                '```\n\n'
                'Commands:\n'
                '/start - Select or create a sheet\n'
                '/sheets - List available sheets\n'
                '/columns - Show columns in current sheet\n'
                '/help - Show this help message'
            ),
            'parse_mode': ParseMode.MARKDOWN
        }
    
    @staticmethod
    def build_sheet_selected_message(sheet_name: str) -> Dict[str, Any]:
        """Build sheet selected message."""
        return {
            'text': (
                f'Selected sheet: "{sheet_name}"\n\n'
                'Send me data in this format:\n'
                '```\n'
                'field1: value1\n'
                'field2: value2\n'
                'field3: value3\n'
                '```'
            ),
            'parse_mode': ParseMode.MARKDOWN
        }
    
    @staticmethod
    def build_new_column_confirmation(column: str, sheet_name: str, keyboard: InlineKeyboardMarkup) -> Dict[str, Any]:
        """Build new column confirmation message."""
        return {
            'text': f'Found new column "{column}". Add it to the sheet?',
            'reply_markup': keyboard
        }
    
    @staticmethod
    def build_error_message(error: str) -> Dict[str, Any]:
        """Build error message."""
        return {
            'text': f'❌ Error: {error}',
            'parse_mode': ParseMode.MARKDOWN
        }
    
    @staticmethod
    def build_success_message(message: str) -> Dict[str, Any]:
        """Build success message."""
        return {
            'text': f'✅ {message}',
            'parse_mode': ParseMode.MARKDOWN
        }
