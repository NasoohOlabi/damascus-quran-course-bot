from typing import Dict

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from ..keyboards.keyboard_builder import KeyboardBuilder
from ..services.sheets_service import SheetsService
from ..states.data_entry_states import CHOOSE_ACTION, SELECT_SHEET, ENTER_DATA


class DataEntryHandler:
    """Handler for data entry conversation flow."""
    
    def __init__(self, sheets_service: SheetsService):
        self.sheets_service = sheets_service
        self.keyboard_builder = KeyboardBuilder()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the conversation and ask user what they want to do."""
        keyboard = [[
            ("📝 Insert Row", "insert_row"),
            ("❌ Cancel", "cancel")
        ]]
        reply_markup = self.keyboard_builder.build_menu_keyboard(keyboard)
        
        await update.message.reply_text(
            "👋 Hi! What would you like to do?",
            reply_markup=reply_markup
        )
        return CHOOSE_ACTION
    
    async def handle_action_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user's action choice."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel":
            await query.edit_message_text("Operation cancelled. Send /start to begin again.")
            return ConversationHandler.END
            
        if query.data == "insert_row":
            sheets = self.sheets_service.get_all_sheets()
            if not sheets:
                await query.edit_message_text("No sheets available. Please create one first.")
                return ConversationHandler.END
                
            keyboard = self.keyboard_builder.build_sheets_keyboard(sheets)
            await query.edit_message_text(
                "Which sheet would you like to add data to?",
                reply_markup=keyboard
            )
            return SELECT_SHEET
            
        return ConversationHandler.END
    
    async def handle_sheet_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle sheet selection and start data entry."""
        query = update.callback_query
        await query.answer()
        
        sheet_name = query.data.split(":")[1]
        context.user_data["current_sheet"] = sheet_name
        context.user_data["columns"] = self.sheets_service.get_columns(sheet_name)
        context.user_data["current_column_index"] = 0
        context.user_data["data"] = {}
        
        await self.prompt_next_column(query, context)
        return ENTER_DATA
    
    async def handle_data_entry(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle user's data input for each column."""
        columns = context.user_data["columns"]
        current_index = context.user_data["current_column_index"]
        current_column = columns[current_index]
        
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
        await update.message.reply_text("Operation cancelled. Send /start to begin again.")
        return ConversationHandler.END
    
    def get_handler(self) -> ConversationHandler:
        """Get the conversation handler."""
        return ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                CHOOSE_ACTION: [
                    CallbackQueryHandler(self.handle_action_choice)
                ],
                SELECT_SHEET: [
                    CallbackQueryHandler(self.handle_sheet_selection, pattern="^select_sheet:")
                ],
                ENTER_DATA: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_data_entry)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )