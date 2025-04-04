from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..config.config import BotConfig
from ..utils.logger import setup_logger
from ..handlers.teacher_management_handler import handle_add_teacher, handle_remove_teacher

logger = setup_logger(__name__)

# Define conversation states
MENU, DATA_ENTRY, PROGRESS, TEACHER = range(4)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and show main menu."""
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
    return MENU

async def handle_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle menu selection."""
    user = update.message.from_user
    choice = update.message.text
    logger.info(f"User {user.first_name} selected: {choice}")

    if choice == "📝 Data Entry":
        await update.message.reply_text(
            "You've selected Data Entry. Please select a sheet:",
            reply_markup=ReplyKeyboardRemove()
        )
        return DATA_ENTRY
    elif choice == "📊 Student Progress":
        await update.message.reply_text(
            "You've selected Student Progress. Please select a student:",
            reply_markup=ReplyKeyboardRemove()
        )
        return PROGRESS
    elif choice == "👨‍🏫 Teacher Management":
        await update.message.reply_text(
            "You've selected Teacher Management. What would you like to do?",
            reply_markup=ReplyKeyboardRemove()
        )
        return TEACHER

    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    await update.message.reply_text(
        "Operation cancelled. Send /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def start_bot(config: BotConfig):
    """Initialize and start the Telegram bot."""
    # Initialize bot application with token
    application = Application.builder().token(config.TOKEN).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", handle_start)],
        states={
            MENU: [MessageHandler(filters.Regex("^(📝 Data Entry|📊 Student Progress|👨‍🏫 Teacher Management)$"), handle_menu_choice)],
            DATA_ENTRY: [MessageHandler(filters.Regex('^(📑 Student Records|📚 Class Progress|📈 Attendance)$'), handle_data_entry_selection)],
            PROGRESS: [MessageHandler(filters.Regex('^👤 .+$'), handle_student_selection)],
            TEACHER: [
                CommandHandler('add', handle_add_teacher),
                CommandHandler('remove', handle_remove_teacher),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_teacher_management)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add conversation handler
    application.add_handler(conv_handler)
    
    logger.info("Bot initialized with conversation handler")
    
    try:
        # Start the bot with polling
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Keep the application running until stopped
        await application.updater.stop()
        await application.stop()
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise
    finally:
        # Ensure proper cleanup
        await application.shutdown()


async def handle_data_entry_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    choice = update.message.text
    logger.info(f"Data Entry selection by {user.first_name}: {choice}")
    await update.message.reply_text(f"You selected {choice}. Please enter the data:")
    return ConversationHandler.END

async def handle_student_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    student = update.message.text[2:]  # Remove emoji prefix
    logger.info(f"Student selected by {user.first_name}: {student}")
    await update.message.reply_text(f"Showing progress for {student}...")
    return ConversationHandler.END

async def handle_teacher_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    action = update.message.text
    logger.info(f"Teacher management action by {user.first_name}: {action}")
    await update.message.reply_text(f"Processing teacher management: {action}")
    return ConversationHandler.END