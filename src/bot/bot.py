import asyncio
import os
from enum import Enum, auto
from pathlib import Path

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config.config import BotConfig
from src.handlers.data_entry_handler import DataEntryHandler

# No longer need to import individual teacher management handlers
# as we're handling all teacher management in the main state machine
from src.services.sheets_service import SheetsService
from src.utils.logger import setup_logger
from src.utils.logging_utils import log_message

logger = setup_logger(__name__)

# Define conversation states as enum for better readability
class State(Enum):
    MENU = auto()
    DATA_ENTRY = auto()
    PROGRESS = auto()
    TEACHER = auto()

@log_message
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and show main menu."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} started the bot")
    
    reply_keyboard = [
        ["📝 Data Entry", "📊 Student Progress"],
        ["👨‍🏫 Teacher Management"]
    ]

    await update.message.reply_text(
        "Welcome to Makin Damascus Bot! 🕌\n\n"
        "I'm here to help manage your Islamic studies program. "
        "Please choose an option below:",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select an option"
        ),
    )
    return State.MENU.value

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle menu selection with detailed logging."""
    user = update.message.from_user
    choice = update.message.text
    logger.info(f"User {user.first_name} selected: {choice}")

    # Store the choice in context for reference in other handlers
    context.user_data['last_menu_choice'] = choice
    
    # Simple switch-like statement for menu routing
    if choice == "📝 Data Entry":
        logger.info(f"Routing user {user.first_name} to Data Entry flow")
        # Instead of just returning DATA_ENTRY state, we'll handle the transition here
        reply_keyboard = [
            ["📑 Student Records", "📚 Class Progress"],
            ["📈 Attendance", "🔙 Back to Menu"]
        ]
        
        await update.message.reply_text(
            "You've selected Data Entry. Please select a sheet type:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select a sheet type"
            )
        )
        return State.DATA_ENTRY.value
        
    elif choice == "📊 Student Progress":
        logger.info(f"Routing user {user.first_name} to Student Progress flow")
        await update.message.reply_text(
            "You've selected Student Progress. Please select a student:",
            reply_markup=ReplyKeyboardRemove()
        )
        return State.PROGRESS.value
        
    elif choice == "👨‍🏫 Teacher Management":
        logger.info(f"Routing user {user.first_name} to Teacher Management flow")
        reply_keyboard = [
            ["➕ Add Teacher", "➖ Remove Teacher"],
            ["📋 List Teachers", "🔙 Back to Menu"]
        ]
        
        await update.message.reply_text(
            "You've selected Teacher Management. What would you like to do?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select an action"
            )
        )
        return State.TEACHER.value

    # Default case - stay in menu
    logger.warning(f"User {user.first_name} made an invalid selection: {choice}")
    await update.message.reply_text("Invalid selection. Please try again.")
    return State.MENU.value

async def handle_data_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle data entry options with detailed logging."""
    user = update.message.from_user
    choice = update.message.text
    logger.info(f"Data Entry selection by {user.first_name}: {choice}")
    
    if choice == "🔙 Back to Menu":
        logger.info(f"User {user.first_name} returning to main menu")
        return await handle_start(update, context)
    
    # Handle different data entry options
    if choice == "📑 Student Records":
        await update.message.reply_text(
            "You selected Student Records. Please enter the student data in the format:\n"
            "Name: [student name]\n"
            "Grade: [grade]\n"
            "Parent: [parent name]\n"
            "Contact: [contact number]",
            reply_markup=ReplyKeyboardRemove()
        )
    elif choice == "📚 Class Progress":
        await update.message.reply_text(
            "You selected Class Progress. Please enter the progress data in the format:\n"
            "Class: [class name]\n"
            "Date: [date]\n"
            "Topic: [topic covered]\n"
            "Notes: [additional notes]",
            reply_markup=ReplyKeyboardRemove()
        )
    elif choice == "📈 Attendance":
        await update.message.reply_text(
            "You selected Attendance. Please enter the attendance data in the format:\n"
            "Class: [class name]\n"
            "Date: [date]\n"
            "Present: [names of present students]\n"
            "Absent: [names of absent students]",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        logger.warning(f"User {user.first_name} made an invalid data entry selection: {choice}")
        await update.message.reply_text("Invalid selection. Please try again.")
        return State.DATA_ENTRY.value
    
    # For now, we'll just return to the menu after displaying instructions
    # In a real implementation, you would process the data entry here
    return State.MENU.value

async def handle_student_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle student progress selection with detailed logging."""
    user = update.message.from_user
    choice = update.message.text
    logger.info(f"Student Progress selection by {user.first_name}: {choice}")
    
    # Here you would implement the logic to show student progress
    await update.message.reply_text(f"Showing progress for {choice}...")
    
    # Return to main menu
    return await handle_start(update, context)

async def handle_teacher_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle teacher management options with detailed logging."""
    user = update.message.from_user
    choice = update.message.text
    logger.info(f"Teacher Management selection by {user.first_name}: {choice}")
    
    if choice == "🔙 Back to Menu":
        logger.info(f"User {user.first_name} returning to main menu")
        return await handle_start(update, context)
    
    # Handle different teacher management options
    if choice == "➕ Add Teacher":
        await update.message.reply_text(
            "Please enter the teacher's information in the format:\n"
            "Name: [teacher name]\n"
            "Email: [email]\n"
            "Phone: [phone number]\n"
            "Specialization: [quran/tajweed/both]",
            reply_markup=ReplyKeyboardRemove()
        )
    elif choice == "➖ Remove Teacher":
        await update.message.reply_text(
            "Please enter the name of the teacher to remove:",
            reply_markup=ReplyKeyboardRemove()
        )
    elif choice == "📋 List Teachers":
        await update.message.reply_text(
            "Here is the list of teachers:\n\n"
            "[This would be populated with actual teacher data]",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        logger.warning(f"User {user.first_name} made an invalid teacher management selection: {choice}")
        await update.message.reply_text("Invalid selection. Please try again.")
        return State.TEACHER.value
    
    # Return to main menu after action
    return await handle_start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation with detailed logging."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    await update.message.reply_text(
        "Operation cancelled. Send /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

class BotRestartHandler(FileSystemEventHandler):
    def __init__(self, restart_callback):
        self.restart_callback = restart_callback

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            logger.info(f"Detected file change: {event.src_path}")
            asyncio.run(self.restart_callback())

async def start_bot(config: BotConfig):
    """Initialize and start the Telegram bot with hot reload."""
    restart_event = asyncio.Event()
    
    async def run_bot():
        nonlocal restart_event
        
        # Initialize bot application with token
        application = Application.builder().token(config.TOKEN).build()
        
        # Initialize services
        sheets_service = SheetsService()
        
        # Create conversation handler with the state machine
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", handle_start)],
            states={
                # Main menu state
                State.MENU.value: [
                    MessageHandler(filters.Regex("^(📝 Data Entry|📊 Student Progress|👨‍🏫 Teacher Management)$"), handle_menu_choice)
                ],
                # Data entry state - handle with text messages instead of nested handler
                State.DATA_ENTRY.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_data_entry)
                ],
                # Progress state
                State.PROGRESS.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_student_progress)
                ],
                # Teacher management state
                State.TEACHER.value: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_teacher_management)
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        # Add conversation handler
        application.add_handler(conv_handler)
        
        logger.info("Bot initialized with state machine conversation handler")
        
        try:
            await application.run_polling(close_loop=False)
        except Exception as e:
            logger.error(f"Bot stopped with error: {str(e)}")
        finally:
            await application.updater.stop()
            await application.shutdown()
            restart_event.set()
    
    # Start file watcher
    observer = Observer()
    event_handler = BotRestartHandler(lambda: run_bot())
    observer.schedule(event_handler, Path(__file__).parent.parent.parent, recursive=True)
    observer.start()
    
    try:
        await run_bot()
    finally:
        observer.stop()
        observer.join()