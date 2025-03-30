from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Dict, Any

from ..services.sheets_service import SheetsService

async def handle_student_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, sheets_service: SheetsService) -> None:
    """Handle the /progress command for managing student progress."""
    # Create StudentProgress sheet if it doesn't exist
    if "StudentProgress" not in sheets_service.get_all_sheets():
        sheets_service.create_sheet("StudentProgress")
        sheets_service.freeze_rows("StudentProgress", 2)
        
        # Add required columns
        progress_columns = [
            "student_name",
            "notes",
            "pages",
            "sura",
            "date",
            "created",
            "created_by",
            "last_modified",
            "last_modified_by"
        ]
        sheets_service.add_columns("StudentProgress", progress_columns)
        
        # Add validation rules in second row
        validation_rules = [
            "list:Students!A:A",  # student_name - must be from Students sheet
            "",  # notes - no validation
            "regex:^[0-9,-]*$",  # pages - numbers and hyphens only
            "",  # sura - no specific validation
            "",  # date
            "",  # created
            "",  # created_by
            "",  # last_modified
            ""   # last_modified_by
        ]
        sheets_service.update_row("StudentProgress", 1, validation_rules)
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Progress Note", callback_data="add_progress")],
        [InlineKeyboardButton("📋 View Progress", callback_data="view_progress")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Student Progress Management\n\n"
        "What would you like to do?",
        reply_markup=reply_markup
    )