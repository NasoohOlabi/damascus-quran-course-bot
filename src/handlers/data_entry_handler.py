from typing import Dict

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from ..keyboards.keyboard_builder import KeyboardBuilder
from ..services.sheets_service import SheetsService
from ..states.data_entry_states import CHOOSE_ACTION, ENTER_DATA, SELECT_SHEET
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class DataEntryHandler:
    """Handler for data entry conversation flow."""
    
    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.keyboard_builder = KeyboardBuilder()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the conversation and ask user what they want to do."""
        logger.debug(f"DataEntryHandler.start() called by {update.message.from_user.id}")
        reply_keyboard = [
            ["📑 Student Records", "📚 Class Progress"],
            ["📈 Attendance"]
        ]
        
        await update.message.reply_text(
            "You've selected Data Entry. Please select a sheet:",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select a sheet"
            )
        )
        return CHOOSE_ACTION
    
    async def handle_action_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user's sheet selection for data entry."""
        # Check if this is a callback query or a text message
        if update.callback_query:
            user = update.callback_query.from_user
            query = update.callback_query
            await query.answer()
            choice = query.data
            message_obj = query.message
            logger.info(f"Data Entry callback selection by {user.first_name}: {choice}")
        else:
            user = update.message.from_user
            choice = update.message.text
            message_obj = update.message
            logger.info(f"Data Entry text selection by {user.first_name}: {choice}")
        
        logger.debug(f"User {user.id} selected option: {choice}")
        
        # Log the input type and choice for debugging
        logger.debug(f"Input type: {'callback' if update.callback_query else 'text'}, Choice: {choice}")
        
        if choice == "📑 Student Records":
            await message_obj.reply_text(
                "You selected Student Records. Please enter the data:",
                reply_markup=ReplyKeyboardRemove()
            )
        elif choice == "📚 Class Progress":
            await message_obj.reply_text(
                "You selected Class Progress. Please enter the data:",
                reply_markup=ReplyKeyboardRemove()
            )
        elif choice == "📈 Attendance":
            await message_obj.reply_text(
                "You selected Attendance. Please enter the data:",
                reply_markup=ReplyKeyboardRemove()
            )
        elif choice == "🔙 Back to Menu":
            # Handle back to menu option
            reply_keyboard = [
                ["📝 Data Entry", "📊 Student Progress"],
                ["👨‍🏫 Teacher Management"]
            ]
            await message_obj.reply_text(
                "Returning to main menu. Please select an option:",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True, input_field_placeholder="Select an option"
                )
            )
            return -1  # Return to previous state
        else:
            # Handle unknown choice
            await message_obj.reply_text(
                "Unknown option. Please select a valid option.",
                reply_markup=ReplyKeyboardRemove()
            )
            return CHOOSE_ACTION
            
        return ENTER_DATA

    # Remove these incorrectly indented lines as they seem to be part of a different method
    # and are causing syntax errors
    #    await query.edit_message_text("No sheets available. Please create one first.")
    #    return ConversationHandler.END
    #    
    #    keyboard = self.keyboard_builder.build_sheets_keyboard(sheets)
    #    await query.edit_message_text(
    #        "Which sheet would you like to add data to?",
    #        reply_markup=keyboard
    #    )
    #    return SELECT_SHEET
    #    
    #    return ConversationHandler.END
    
    async def handle_sheet_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle sheet selection and start data entry."""
        query = update.callback_query
        await query.answer()
        logger.debug(f"Sheet selection callback from user {query.from_user.id}")
        
        sheet_name = query.data.split(":")[1]
        context.user_data["current_sheet"] = sheet_name
        context.user_data["columns"] = self.sheets_service.get_columns(sheet_name)
        context.user_data["current_column_index"] = 0
        context.user_data["data"] = {}
        
        await self.prompt_next_column(query, context)
        return ENTER_DATA
    
    async def handle_data_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user's data input for each column."""
        logger.debug(f"Data entry from user {update.message.from_user.id}")
        columns = context.user_data["columns"]
        current_index = context.user_data["current_column_index"]
        current_column = columns[current_index]
        logger.debug(f"Processing column {current_column} (index {current_index}) for sheet {context.user_data.get('current_sheet')}")
        
        # Store the value
        context.user_data["data"][current_column] = update.message.text
        
        # Move to next column
        context.user_data["current_column_index"] += 1
        
        # Check if we're done
        if context.user_data["current_column_index"] >= len(columns):
            sheet_name = context.user_data["current_sheet"]
            data = context.user_data["data"]
            
            try:
                self.sheets_service.append_row(sheet_name, data)
                await update.message.reply_text("✅ Data successfully added!")
            except ValueError as e:
                await update.message.reply_text(f"❌ Error: {str(e)}")
            
            return ConversationHandler.END
        
        # Prompt for next column
        await self.prompt_next_column(update.message, context)
        return ENTER_DATA
    
    async def prompt_next_column(self, message, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Prompt user for the next column value."""
        columns = context.user_data["columns"]
        current_index = context.user_data["current_column_index"]
        current_column = columns[current_index]
        
        await message.reply_text(
            f"Please enter the value for: *{current_column}*",
            parse_mode='Markdown'
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        logger.debug(f"Conversation cancelled by user {update.message.from_user.id}")
        await update.message.reply_text("Operation cancelled. Send /start to begin again.")
        return ConversationHandler.END
    
    def get_handler(self) -> ConversationHandler:
        """Get the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                CHOOSE_ACTION: [
                    # Accept both text messages and callback queries for action choice
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_action_choice),
                    CallbackQueryHandler(self.handle_action_choice)
                ],
                SELECT_SHEET: [
                    CallbackQueryHandler(self.handle_sheet_selection, pattern="^select_sheet:")
                ],
                ENTER_DATA: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_data_entry)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            per_message=False,
            per_chat=True
        )