import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_messages.log'
)

logger = logging.getLogger(__name__)

def log_message(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.message:
            user = update.effective_user
            logger.info(
                f"Message received from {user.id} ({user.username or 'no username'}): "
                f"'{update.message.text}' in chat {update.effective_chat.id}"
            )
        return await func(update, context, *args, **kwargs)
    return wrapper