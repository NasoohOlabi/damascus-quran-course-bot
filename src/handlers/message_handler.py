from telegram import Update
from telegram.ext import ContextTypes
from ..keyboards.keyboard_builder import KeyboardBuilder
from ..utils.logger import setup_logger

logger = setup_logger(__name__)
keyboard_builder = KeyboardBuilder()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and commands."""
    try:
        # Check if this is a command
        if update.message.text.startswith('/'):
            await handle_command(update, context)
        else:
            await handle_text_message(update, context)
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot commands."""
    if update.message.text == '/start':
        keyboard = [
            [("📝 Data Entry", "/entry")],
            [("📊 Student Progress", "/progress")],
            [("👨‍🏫 Teacher Management", "/teacher")]
        ]
        reply_markup = keyboard_builder.build_menu_keyboard(keyboard)
        
        await update.message.reply_text(
            "Welcome to Makin Damascus Bot! 🕌\n\n"
            "I'm here to help manage your Islamic studies program. "
            "Please choose an option below:",
            reply_markup=reply_markup
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle non-command text messages."""
    await update.message.reply_text(
        "Please use the menu commands to interact with me. "
        "Send /start to see available options."
    )