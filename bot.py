import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

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

# Initialize the items table (will create if doesn't exist)
ITEMS_TABLE = "Items"
try:
    sheets.get_table(ITEMS_TABLE)
except Exception as e:
    # Create the table with initial schema
    sheets.write_range(f"{ITEMS_TABLE}!A1:C1", [["name", "description", "category"]])
    sheets.init_table(ITEMS_TABLE)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(
        f'Hi {user.first_name}! I am the Makin Damascus bot. '
        'I can help you interact with our database.\n\n'
        'Available commands:\n'
        '/help - Show this help message\n'
        '/add <name> | <description> | <category> - Add an item\n'
        '/list - List all items\n'
        '/search <column> <value> - Search items (exact match)\n'
        '/fuzzy <column> <value> - Search items (fuzzy match)\n'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        'Available commands:\n'
        '/help - Show this help message\n'
        '/add <name> | <description> | <category> - Add an item\n'
        '/list - List all items\n'
        '/search <column> <value> - Search items (exact match)\n'
        '/fuzzy <column> <value> - Search items (fuzzy match)\n'
    )

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add an item to the database."""
    if not context.args:
        await update.message.reply_text(
            'Please provide item details in the format:\n'
            '/add <name> | <description> | <category>'
        )
        return

    # Join all arguments and split by pipe
    item_data = ' '.join(context.args).split('|')
    if len(item_data) != 3:
        await update.message.reply_text(
            'Please provide all required fields:\n'
            '/add <name> | <description> | <category>'
        )
        return

    # Create item dictionary
    item = {
        'name': item_data[0].strip(),
        'description': item_data[1].strip(),
        'category': item_data[2].strip()
    }

    try:
        sheets.append_row(ITEMS_TABLE, item)
        await update.message.reply_text(f'Added item "{item["name"]}" to the database.')
    except Exception as e:
        logger.error(f"Error adding item: {e}")
        await update.message.reply_text('Sorry, there was an error adding the item.')

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all items in the database."""
    try:
        items = sheets.read_range(f"{ITEMS_TABLE}!A:C")
        if not items or len(items) <= 1:  # Only header row or empty
            await update.message.reply_text('No items in the database.')
            return

        message = "Items in database:\n\n"
        for item in items[1:]:  # Skip header row
            name = item[0] if len(item) > 0 else 'N/A'
            desc = item[1] if len(item) > 1 else 'N/A'
            category = item[2] if len(item) > 2 else 'N/A'
            message += f"📌 {name}\n   Description: {desc}\n   Category: {category}\n\n"
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error listing items: {e}")
        await update.message.reply_text('Sorry, there was an error retrieving the items.')

async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for items in the database (exact match)."""
    if len(context.args) < 2:
        await update.message.reply_text(
            'Please provide search details:\n'
            '/search <column> <value>'
        )
        return

    column = context.args[0].lower()
    value = ' '.join(context.args[1:])

    try:
        results = sheets.search_column(ITEMS_TABLE, column, value, exact=True)
        if not results:
            await update.message.reply_text(f'No items found matching "{value}" in column "{column}".')
            return

        message = f"Found {len(results)} matching items:\n\n"
        for item in results:
            message += f"📌 {item['name']}\n   Description: {item['description']}\n   Category: {item['category']}\n\n"
        
        await update.message.reply_text(message)
    except ValueError as e:
        await update.message.reply_text(f'Error: {str(e)}')
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        await update.message.reply_text('Sorry, there was an error searching for items.')

async def fuzzy_search_items(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for items in the database (fuzzy match)."""
    if len(context.args) < 2:
        await update.message.reply_text(
            'Please provide search details:\n'
            '/fuzzy <column> <value>'
        )
        return

    column = context.args[0].lower()
    value = ' '.join(context.args[1:])

    try:
        results = sheets.fuzzy_search_column(ITEMS_TABLE, column, value)
        if not results:
            await update.message.reply_text(f'No items found similar to "{value}" in column "{column}".')
            return

        message = f"Found {len(results)} similar items (sorted by similarity):\n\n"
        for item, distance in results[:5]:  # Show top 5 results
            message += f"📌 {item['name']} (similarity: {100 - (distance * 100 / max(len(value), 1)):.0f}%)\n"
            message += f"   Description: {item['description']}\n"
            message += f"   Category: {item['category']}\n\n"
        
        if len(results) > 5:
            message += f"(Showing top 5 of {len(results)} results)"
        
        await update.message.reply_text(message)
    except ValueError as e:
        await update.message.reply_text(f'Error: {str(e)}')
    except Exception as e:
        logger.error(f"Error searching items: {e}")
        await update.message.reply_text('Sorry, there was an error searching for items.')

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("list", list_items))
    application.add_handler(CommandHandler("search", search_items))
    application.add_handler(CommandHandler("fuzzy", fuzzy_search_items))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 