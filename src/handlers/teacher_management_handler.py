from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from src.services.sheets_service import SheetsService

async def handle_teacher_management(update: Update, context: ContextTypes.DEFAULT_TYPE, sheets_service: SheetsService) -> None:
    """Handle the /teachers command for managing teachers."""
    # Create Teachers sheet if it doesn't exist
    if "Teachers" not in sheets_service.get_all_sheets():
        sheets_service.create_sheet("Teachers")
        sheets_service.freeze_rows("Teachers", 2)
        
        # Add required columns
        teacher_columns = [
            "name",
            "email",
            "phone",
            "status",  # active/suspended/inactive
            "specialization",  # quran/tajweed/both
            "join_date",
            "notes",
            "created",
            "created_by",
            "last_modified",
            "last_modified_by"
        ]
        sheets_service.add_columns("Teachers", teacher_columns)
        
        # Add validation rules in second row
        validation_rules = [
            "",  # name - no validation
            "regex:^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",  # email format
            "regex:^\\+?[1-9]\\d{1,14}$",  # phone - international format
            "list:active,suspended,inactive",  # status
            "list:quran,tajweed,both",  # specialization
            "",  # join_date
            "",  # notes
            "",  # created
            "",  # created_by
            "",  # last_modified
            ""   # last_modified_by
        ]
        sheets_service.update_row("Teachers", 1, validation_rules)
    
    keyboard = [
        [InlineKeyboardButton("➕ Add New Teacher", callback_data="add_teacher")],
        [InlineKeyboardButton("📋 List Teachers", callback_data="list_teachers")],
        [InlineKeyboardButton("🔄 Update Teacher Status", callback_data="update_teacher_status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Teacher Management\n\n"
        "What would you like to do?",
        reply_markup=reply_markup
    )

async def handle_add_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter the teacher's name:")
    return TEACHER

async def handle_remove_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please select a teacher to remove:")
    return TEACHER