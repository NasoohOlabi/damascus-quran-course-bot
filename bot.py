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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

# Initialize sheets manager
sheets = SheetsManager()

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
    """Send a message when the command /help is issued."""
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
    
    if query.data == "create_sheet":
        context.user_data['awaiting_sheet_name'] = True
        await query.message.reply_text(
            "Please send me the name for the new sheet:"
        )
        return
        
    if query.data.startswith("select_sheet:"):
        sheet_name = query.data.split(":", 1)[1]
        context.user_data['current_sheet'] = sheet_name
        await query.message.reply_text(
            f'Selected sheet: "{sheet_name}"\n\n'
            'Send me data in this format:\n'
            '```\n'
            'field1: value1\n'
            'field2: value2\n'
            'field3: value3\n'
            '```',
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    if context.user_data.get('awaiting_sheet_name'):
        # Create new sheet
        sheet_name = update.message.text.strip()
        try:
            sheets.create_sheet(sheet_name)
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

def main() -> None:
    """Start the bot."""
    # Configure the application with custom settings
    defaults = {
        "connect_timeout": 30.0,  # Increase connection timeout
        "read_timeout": 30.0,    # Increase read timeout
        "write_timeout": 30.0,   # Increase write timeout
        "tzinfo": None  # Set timezone info to None to use system default
    }
    
    application = (
        Application.builder()
        .token(TOKEN)
        .defaults(defaults)
        .get_updates_connect_timeout(30.0)  # Increase get_updates connection timeout
        .get_updates_read_timeout(30.0)     # Increase get_updates read timeout
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sheets", list_sheets))
    application.add_handler(CommandHandler("columns", show_columns))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Configure error handling
    application.add_error_handler(error_handler)

    # Start the Bot with reconnection logic
    while True:
        try:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,  # Ignore updates that occurred while the bot was offline
                timeout=30,                 # Increase polling timeout
            )
        except (TimedOut, NetworkError) as e:
            logger.error(f"Connection error: {e}")
            logger.info("Waiting 10 seconds before retrying...")
            import time
            time.sleep(10)
            continue
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            break

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram bot."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if isinstance(context.error, TimedOut):
        logger.info("Connection timed out. Will retry automatically.")
        return
    
    if isinstance(context.error, NetworkError):
        logger.info("Network error occurred. Will retry automatically.")
        return
    
    # For any other errors, log them but don't crash
    logger.error("Update '%s' caused error '%s'", update, context.error)

if __name__ == '__main__':
    main() 