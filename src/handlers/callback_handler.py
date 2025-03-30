from telegram import Update
from telegram.ext import ContextTypes
from ..utils.logger import setup_logger
from .data_entry_handler import handle_data_entry
from .student_progress_handler import handle_student_progress
from .teacher_management_handler import handle_teacher_management

logger = setup_logger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboard buttons."""
    try:
        query = update.callback_query
        await query.answer()
        
        # Map callback data to appropriate handlers
        command_map = {
            '/entry': handle_data_entry,
            '/progress': handle_student_progress,
            '/teacher': handle_teacher_management
        }
        
        # Get the command from callback data
        command = query.data
        
        if command in command_map:
            # Call the appropriate handler
            await command_map[command](update, context)
        else:
            logger.warning(f"Unhandled callback query: {command}")
            await query.message.reply_text(
                "Sorry, I don't recognize that option. "
                "Please try using the menu again with /start."
            )
            
    except Exception as e:
        logger.error(f"Error handling callback: {str(e)}")
        await update.callback_query.message.reply_text(
            "Sorry, something went wrong. Please try again."
        )