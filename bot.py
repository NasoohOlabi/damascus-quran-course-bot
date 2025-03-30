import asyncio
import logging
import os
from datetime import timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from sheets_manager import SheetsManager
from src.handlers.data_entry_handler import DataEntryHandler
from src.services.sheets_service import SheetsService
from telegram import KeyboardButton, ReplyKeyboardMarkup

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
if not SPREADSHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID not found in environment variables")

# Initialize sheets manager and service
sheets = SheetsManager()
with open('credentials.json') as f:
    import json
    credentials = json.load(f)
sheets_service = SheetsService(credentials, SPREADSHEET_ID)

def parse_object(text: str) -> Optional[Dict[str, Any]]:
    """Parse an object from message text."""
    try:
        result = {}
        for line in text.strip().split('\n'):
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                result[key] = value
        return result if result else None
    except Exception as e:
        logger.error(f"Error parsing object: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    sheets_list = sheets.get_all_sheets()
    
    keyboard = []
    for sheet_name in sheets_list:
        keyboard.append([InlineKeyboardButton(sheet_name, callback_data=f"select_sheet:{sheet_name}")])
    keyboard.append([InlineKeyboardButton("➕ Create New Sheet", callback_data="create_sheet")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f'Hi {user.first_name}! Welcome to the Makin Damascus bot.\n\n'
        'Please select a sheet to work with or create a new one:',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
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
        '/students - Manage students\n'  # Add this line
        '/help - Show this help message',
        parse_mode='Markdown'
    )

async def list_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all available sheets."""
    sheets_list = sheets.get_all_sheets()
    
    keyboard = []
    for sheet_name in sheets_list:
        keyboard.append([InlineKeyboardButton(sheet_name, callback_data=f"select_sheet:{sheet_name}")])
    keyboard.append([InlineKeyboardButton("➕ Create New Sheet", callback_data="create_sheet")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Available sheets:\n'
        'Click to select a sheet:',
        reply_markup=reply_markup
    )

async def show_columns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show columns in the current sheet."""
    if not context.user_data.get('current_sheet'):
        await update.message.reply_text(
            'Please select a sheet first using /start or /sheets'
        )
        return

    sheet_name = context.user_data['current_sheet']
    columns = sheets.get_columns(sheet_name)
    
    if not columns:
        await update.message.reply_text(
            f'Sheet "{sheet_name}" has no columns yet.\n'
            'Send some data to create columns!'
        )
        return

    await update.message.reply_text(
        f'Columns in sheet "{sheet_name}":\n' +
        '\n'.join(f'• {col}' for col in columns)
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "add_student":
        context.user_data['current_sheet'] = "Students"
        context.user_data['adding_student'] = True
        context.user_data['pending_data'] = {}
        
        # Start with student name
        await query.message.reply_text(
            "Please enter the student's name:",
            parse_mode='Markdown'
        )
        return
        
    if query.data == "list_students":
        # Get students from sheet
        students = sheets.get_values("Students", "A2:E")  # Get name, age, teacher, status, join_date
        if not students:
            await query.message.reply_text("No students found.")
            return
            
        # Format student list
        response = "📋 *Student List*\n\n"
        for student in students:
            name = student[0] if len(student) > 0 else "N/A"
            teacher = student[2] if len(student) > 2 else "N/A"
            status = student[3] if len(student) > 3 else "N/A"
            response += f"*{name}*\n"
            response += f"Teacher: {teacher}\n"
            response += f"Status: {status}\n\n"
        
        await query.message.reply_text(response, parse_mode='Markdown')
        return

    if query.data.startswith("add_column:"):
        # Handle add column confirmation
        sheet_name, column = query.data.split(":", 2)[1:]
        sheets.add_columns(sheet_name, [column])
        
        # Reset the data entry flow with updated columns
        columns = sheets.get_columns(sheet_name)
        context.user_data['pending_data'] = {}
        context.user_data['columns'] = columns
        context.user_data['current_column_index'] = 0
        
        # Start asking for values
        await query.message.reply_text(
            f'Column added. Let\'s fill in the data!\n'
            f'Please enter a value for: *{columns[0]}*',
            parse_mode='Markdown'
        )
        return

    if query.data.startswith("select_sheet:"):
        sheet_name = query.data.split(":", 1)[1]
        context.user_data['current_sheet'] = sheet_name
        
        # Get columns and prepare for data entry
        columns = sheets.get_columns(sheet_name)
        if not columns:
            await query.message.reply_text(
                f'Sheet "{sheet_name}" has no columns yet.\n'
                'Please add some data first to create columns!'
            )
            return
            
        context.user_data['pending_data'] = {}
        context.user_data['columns'] = columns
        context.user_data['current_column_index'] = 0
        
        # Ask for the first column
        await query.message.reply_text(
            f'Selected sheet: "{sheet_name}"\n'
            f'Please enter a value for: *{columns[0]}*',
            parse_mode='Markdown'
        )
        return
        
    if query.data.startswith("add_column:"):
        # Handle add column confirmation
        sheet_name, column = query.data.split(":", 2)[1:]
        sheets.add_columns(sheet_name, [column])
        # Remove the pending column from context
        if 'pending_columns' in context.user_data:
            context.user_data['pending_columns'].remove(column)
        
        if context.user_data.get('pending_data'):
            # Try to add the data again
            await handle_object_data(
                context.user_data['pending_data'],
                sheet_name,
                query.message,
                context
            )
        return
        
    if query.data.startswith("skip_column:"):
        # Handle skip column
        _, column = query.data.split(":", 1)
        if 'pending_columns' in context.user_data:
            context.user_data['pending_columns'].remove(column)
            
        if context.user_data.get('pending_data'):
            # Try to add the data again
            await handle_object_data(
                context.user_data['pending_data'],
                context.user_data['current_sheet'],
                query.message,
                context
            )

async def handle_object_data(data: Dict[str, Any], sheet_name: str, message: Any, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle parsed object data."""
    # Get current columns
    current_columns = sheets.get_columns(sheet_name)
    
    # Add audit data
    user = message.from_user
    timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Add audit fields to the data
    if not current_columns:  # New sheet
        data["created"] = timestamp
        data["created_by"] = user.username or user.first_name
    data["last_modified"] = timestamp
    data["last_modified_by"] = user.username or user.first_name
    
    # Find new columns
    new_columns = []
    for col in data.keys():
        if col not in current_columns:
            new_columns.append(col)
    
    # If there are new columns, ask for confirmation
    if new_columns:
        if 'pending_columns' not in context.user_data:
            context.user_data['pending_columns'] = new_columns
            context.user_data['pending_data'] = data
        
        if not context.user_data['pending_columns']:
            # All columns have been handled
            sheets.append_row(sheet_name, data)
            await message.reply_text("✅ Data added successfully!")
            context.user_data.pop('pending_data', None)
            return
            
        # Ask about the next column
        column = context.user_data['pending_columns'][0]
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"add_column:{sheet_name}:{column}"),
                InlineKeyboardButton("❌ No", callback_data=f"skip_column:{column}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f'Found new column "{column}". Add it to the sheet?',
            reply_markup=reply_markup
        )
        return
    
    # If no new columns, just add the data
    sheets.append_row(sheet_name, data)
    await message.reply_text("✅ Data added successfully!")

# Add after the imports
import re

def get_validation_rule(sheet_name: str, column: str, sheets: SheetsManager) -> Tuple[Optional[str], Optional[str]]:
    """Get validation rule from the second row of the sheet."""
    try:
        values = sheets.get_values(sheet_name, "1:2")  # Get first two rows
        if len(values) < 2:
            return None, None
            
        headers = values[0]
        rules = values[1]
        
        for i, header in enumerate(headers):
            if header == column and i < len(rules):
                rule = rules[i]
                if rule.startswith("regex:"):
                    return "regex", rule[6:]
                elif rule.startswith("list:"):
                    return "list", rule[5:]
        return None, None
    except Exception as e:
        logger.error(f"Error getting validation rule: {e}")
        return None, None

def validate_value(sheet_name: str, column: str, value: str, sheets: SheetsManager) -> Tuple[bool, Optional[str]]:
    """Validate a value based on the sheet's validation rules."""
    rule_type, rule_value = get_validation_rule(sheet_name, column, sheets)
    
    if rule_type == "regex":
        if not re.match(rule_value, value):
            return False, f"Value must match pattern: {rule_value}"
    
    elif rule_type == "list":
        try:
            valid_values = sheets.get_values(rule_value)
            flat_values = [str(v[0]).strip() for v in valid_values if v]
            if value not in flat_values:
                return False, f"Value must be one of: {', '.join(flat_values)}"
        except Exception as e:
            logger.error(f"Error checking list values: {e}")
            return True, None
    
    return True, None

# Modify handle_message function's column-based data entry section
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('awaiting_sheet_name'):
        # Create new sheet
        sheet_name = update.message.text.strip()
        try:
            sheets.create_sheet(sheet_name)
            # Freeze first two rows
            sheets_service.freeze_rows(sheet_name, 2)
            
            # Add audit columns
            audit_columns = ["created", "created_by", "last_modified", "last_modified_by"]
            sheets.add_columns(sheet_name, audit_columns)
            
            context.user_data['current_sheet'] = sheet_name
            context.user_data['awaiting_sheet_name'] = False
            await update.message.reply_text(
                f'Created sheet: "{sheet_name}"\n\n'
                'Send me data in this format:\n'
                '```\n'
                'field1: value1\n'
                'field2: value2\n'
                'field3: value3\n'
                '```',
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error creating sheet: {e}")
            await update.message.reply_text(
                f'Sorry, could not create sheet. Please try another name.'
            )
        return

    if context.user_data.get('columns') and 'current_column_index' in context.user_data:
        columns = context.user_data['columns']
        current_index = context.user_data['current_column_index']
        current_column = columns[current_index]
        sheet_name = context.user_data['current_sheet']
        value = update.message.text.strip()
        
        # Validate the value
        is_valid, error_message = validate_value(sheet_name, current_column, value, sheets)
        if not is_valid:
            await update.message.reply_text(
                f"❌ Invalid value for {current_column}: {error_message}\n"
                "Please try again:",
                parse_mode='Markdown'
            )
            return
        
        # Store the valid value and continue with existing code...
        context.user_data['pending_data'][current_column] = value
        
        # Rest of the handler remains the same...

    if not context.user_data.get('current_sheet'):
        await update.message.reply_text(
            'Please select a sheet first using /start or /sheets'
        )
        return

    # Try to parse object data
    data = parse_object(update.message.text)
    if not data:
        await update.message.reply_text(
            'Please send data in this format:\n'
            '```\n'
            'field1: value1\n'
            'field2: value2\n'
            'field3: value3\n'
            '```',
            parse_mode='Markdown'
        )
        return

    await handle_object_data(
        data,
        context.user_data['current_sheet'],
        update.message,
        context
    )

async def handle_change_spreadsheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /change_spreadsheet command."""
    # Check if user is owner
    if str(update.effective_user.id) != os.getenv('OWNER_ID'):
        await update.message.reply_text("This command is only available to the bot owner.")
        return
    
    # Ask for new spreadsheet name
    await update.message.reply_text(
        "Please enter the name for the new spreadsheet:\n\n"
        "Note: This will create a new Google Spreadsheet with all necessary sheets."
    )
    return AWAIT_SPREADSHEET_NAME

# Add state constants
AWAIT_SPREADSHEET_NAME = 'AWAIT_SPREADSHEET_NAME'
AWAIT_COPY_CONFIRMATION = 'AWAIT_COPY_CONFIRMATION'

async def handle_spreadsheet_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the new spreadsheet name input."""
    new_spreadsheet_name = update.message.text.strip()
    
    try:
        # Create new spreadsheet
        result = sheets_service.create_sheet(new_spreadsheet_name)
        new_spreadsheet_id = sheets_service.spreadsheet_id
        
        # Store the old spreadsheet ID for potential data migration
        context.user_data['old_spreadsheet_id'] = SPREADSHEET_ID
        context.user_data['new_spreadsheet_id'] = new_spreadsheet_id
        
        # Ask if user wants to copy students and teachers data
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data="copy_data:yes"),
             InlineKeyboardButton("No", callback_data="copy_data:no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"New spreadsheet '{new_spreadsheet_name}' created successfully!\n\n"
            "Would you like to copy existing students and teachers data to the new spreadsheet?",
            reply_markup=reply_markup
        )
        
        return AWAIT_COPY_CONFIRMATION
        
    except Exception as e:
        await update.message.reply_text(f"Error creating spreadsheet: {str(e)}")
        return ConversationHandler.END

async def handle_copy_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the confirmation for copying data."""
    query = update.callback_query
    await query.answer()
    
    choice = query.data.split(':')[1]
    
    if choice == 'yes':
        try:
            old_id = context.user_data['old_spreadsheet_id']
            new_id = context.user_data['new_spreadsheet_id']
            
            # Create temporary service instances for both spreadsheets
            old_service = SheetsService(credentials, old_id)
            new_service = SheetsService(credentials, new_id)
            
            # Copy students data
            students_data = old_service.get_rows('Students')
            if students_data:
                for row in students_data:
                    new_service.append_row('Students', row)
            
            # Copy teachers data
            teachers_data = old_service.get_rows('Teachers')
            if teachers_data:
                for row in teachers_data:
                    new_service.append_row('Teachers', row)
            
            await query.message.reply_text(
                "✅ Data copied successfully! The bot will now use the new spreadsheet."
            )
        except Exception as e:
            await query.message.reply_text(f"Error copying data: {str(e)}")
    else:
        await query.message.reply_text(
            "✅ New spreadsheet setup complete! The bot will now use the new spreadsheet."
        )
    
    # Update the environment variable
    os.environ['GOOGLE_SHEET_ID'] = context.user_data['new_spreadsheet_id']
    
    # Clean up user data
    context.user_data.pop('old_spreadsheet_id', None)
    context.user_data.pop('new_spreadsheet_id', None)
    
    return ConversationHandler.END

# Add conversation handler for spreadsheet change
spreadsheet_change_handler = ConversationHandler(
    entry_points=[CommandHandler('change_spreadsheet', handle_change_spreadsheet)],
    states={
        AWAIT_SPREADSHEET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spreadsheet_name)],
        AWAIT_COPY_CONFIRMATION: [CallbackQueryHandler(handle_copy_confirmation)]
    },
    fallbacks=[]
)

# Update the main() function to add the new handler
def main() -> None:
    """Start the bot."""
    # Configure the application with custom settings
    application = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sheets", list_sheets))
    application.add_handler(CommandHandler("columns", show_columns))
    application.add_handler(CommandHandler("progress", lambda update, context: handle_student_progress(update, context, sheets_service)))
    # Add near other async functions
    async def handle_students(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /students command."""
        # Create students sheet if it doesn't exist
        if "Students" not in sheets.get_all_sheets():
            sheets.create_sheet("Students")
            sheets_service.freeze_rows("Students", 2)
            
            # Add required columns
            student_columns = [
                "name",
                "age",
                "teacher",
                "status",  # active/inactive
                "join_date",
                "created",
                "created_by",
                "last_modified",
                "last_modified_by"
            ]
            sheets.add_columns("Students", student_columns)
            
            # Add validation rules in second row
            validation_rules = [
                "",  # name - no validation
                "regex:^[0-9]+$",  # age - numbers only
                f"list:Users!A:A",  # teacher - must be from Users sheet
                "list:active,inactive",  # status
                "",  # join_date
                "",  # created
                "",  # created_by
                "",  # last_modified
                ""   # last_modified_by
            ]
            sheets.update_row("Students", 1, validation_rules)  # Add validation rules in second row
        
        keyboard = [
            [InlineKeyboardButton("➕ Add New Student", callback_data="add_student")],
            [InlineKeyboardButton("📋 List Students", callback_data="list_students")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Student Management\n\n"
            "What would you like to do?",
            reply_markup=reply_markup
        )
    
    # Add to handle_callback function
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_student":
            context.user_data['current_sheet'] = "Students"
            context.user_data['adding_student'] = True
            context.user_data['pending_data'] = {}
            
            # Start with student name
            await query.message.reply_text(
                "Please enter the student's name:",
                parse_mode='Markdown'
            )
            return
            
        if query.data == "list_students":
            # Get students from sheet
            students = sheets.get_values("Students", "A2:E")  # Get name, age, teacher, status, join_date
            if not students:
                await query.message.reply_text("No students found.")
                return
                
            # Format student list
            response = "📋 *Student List*\n\n"
            for student in students:
                name = student[0] if len(student) > 0 else "N/A"
                teacher = student[2] if len(student) > 2 else "N/A"
                status = student[3] if len(student) > 3 else "N/A"
                response += f"*{name}*\n"
                response += f"Teacher: {teacher}\n"
                response += f"Status: {status}\n\n"
            
            await query.message.reply_text(response, parse_mode='Markdown')
            return
            
    if query.data == "add_progress":
        context.user_data['current_sheet'] = "StudentProgress"
        context.user_data['adding_progress'] = True
        context.user_data['pending_data'] = {}
        
        # Start with student name
        await query.message.reply_text(
            "Please enter the student's name:",
            parse_mode='Markdown'
        )
        return
        
    if query.data == "view_progress":
        # Get progress notes from sheet
        progress = sheets.get_values("StudentProgress", "A2:E")  # Get student_name, notes, pages, sura, date
        if not progress:
            await query.message.reply_text("No progress notes found.")
            return
            
        # Format progress list
        response = "📋 *Student Progress Notes*\n\n"
        for note in progress:
            student = note[0] if len(note) > 0 else "N/A"
            notes = note[1] if len(note) > 1 else "N/A"
            pages = note[2] if len(note) > 2 else ""
            sura = note[3] if len(note) > 3 else ""
            date = note[4] if len(note) > 4 else "N/A"
            
            response += f"*{student}* - {date}\n"
            response += f"Notes: {notes}\n"
            if pages: response += f"Pages: {pages}\n"
            if sura: response += f"Sura: {sura}\n"
            response += "\n"
        
        await query.message.reply_text(response, parse_mode='Markdown')
        return
        
    # Add to main function
    application.add_handler(CommandHandler("students", handle_students))
    application.add_handler(CommandHandler("columns", show_columns))