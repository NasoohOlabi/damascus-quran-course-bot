from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from src.handlers.message_handler import handle_message
from src.handlers.callback_handler import handle_callback
from src.handlers.data_entry_handler import handle_data_entry
from src.handlers.student_progress_handler import handle_student_progress
from src.handlers.teacher_management_handler import handle_teacher_management
from src.config.config import BotConfig
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def start_bot(config: BotConfig):
    """Initialize and start the Telegram bot."""
    try:
        # Initialize bot application with token
        application = Application.builder().token(config.TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", handle_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Add specific feature handlers
        application.add_handler(CommandHandler("entry", handle_data_entry))
        application.add_handler(CommandHandler("progress", handle_student_progress))
        application.add_handler(CommandHandler("teacher", handle_teacher_management))
        
        logger.info("Bot initialized successfully")
        
        # Start the bot
        await application.initialize()
        await application.start()
        await application.run_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        raise