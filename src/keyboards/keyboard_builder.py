from typing import List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class KeyboardBuilder:
    """Builder class for creating keyboard layouts."""
    
    @staticmethod
    def build_sheets_keyboard(sheets_list: List[str]) -> InlineKeyboardMarkup:
        """Build keyboard with sheet selection buttons."""
        keyboard = []
        for sheet_name in sheets_list:
            keyboard.append([
                InlineKeyboardButton(sheet_name, callback_data=f"select_sheet:{sheet_name}")
            ])
        keyboard.append([
            InlineKeyboardButton("➕ Create New Sheet", callback_data="create_sheet")
        ])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_column_confirmation_keyboard(sheet_name: str, column: str) -> InlineKeyboardMarkup:
        """Build keyboard for column confirmation."""
        keyboard = [[
            InlineKeyboardButton("✅ Yes", callback_data=f"add_column:{sheet_name}:{column}"),
            InlineKeyboardButton("❌ No", callback_data=f"skip_column:{column}")
        ]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_menu_keyboard(buttons: List[Tuple[str, str]]) -> InlineKeyboardMarkup:
        """Build menu keyboard from button tuples (text, callback_data)."""
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for text, callback_data in row:
                keyboard_row.append(InlineKeyboardButton(text, callback_data=callback_data))
            keyboard.append(keyboard_row)
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def build_navigation_keyboard(
        back_callback: Optional[str] = None,
        next_callback: Optional[str] = None,
        done_callback: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """Build navigation keyboard with back/next/done buttons."""
        keyboard = []
        row = []
        
        if back_callback:
            row.append(InlineKeyboardButton("⬅️ Back", callback_data=back_callback))
        if next_callback:
            row.append(InlineKeyboardButton("Next ➡️", callback_data=next_callback))
        if done_callback:
            row.append(InlineKeyboardButton("✅ Done", callback_data=done_callback))
            
        keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)
