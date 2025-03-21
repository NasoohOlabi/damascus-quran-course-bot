from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes

from ..keyboards.keyboard_builder import KeyboardBuilder
from ..messages.message_builder import MessageBuilder
from ..services.sheets_service import SheetsService
from .base_state import State


class SelectSheetState(State):
    """State for selecting or creating a sheet."""
    
    def __init__(self, sheets_service: SheetsService):
        super().__init__()
        self.sheets_service = sheets_service
        
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle sheet name input when creating a new sheet."""
        if not context.user_data.get('awaiting_sheet_name'):
            return
            
        sheet_name = update.message.text.strip()
        try:
            self.sheets_service.create_sheet(sheet_name)
            context.user_data['current_sheet'] = sheet_name
            context.user_data['awaiting_sheet_name'] = False
            
            # Transition to input state
            self.next_state = InputDataState(self.sheets_service)
            
            await update.message.reply_text(
                **MessageBuilder.build_sheet_selected_message(sheet_name)
            )
        except Exception as e:
            await update.message.reply_text(
                **MessageBuilder.build_error_message(str(e))
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle sheet selection or creation callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "create_sheet":
            context.user_data['awaiting_sheet_name'] = True
            await query.message.reply_text("Please send me the name for the new sheet:")
            return
            
        if query.data.startswith("select_sheet:"):
            sheet_name = query.data.split(":", 1)[1]
            context.user_data['current_sheet'] = sheet_name
            
            # Transition to input state
            self.next_state = InputDataState(self.sheets_service)
            
            await query.message.reply_text(
                **MessageBuilder.build_sheet_selected_message(sheet_name)
            )

class InputDataState(State):
    """State for inputting data into a sheet."""
    
    def __init__(self, sheets_service: SheetsService):
        super().__init__()
        self.sheets_service = sheets_service
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle data input for the current sheet."""
        sheet_name = context.user_data.get('current_sheet')
        if not sheet_name:
            await update.message.reply_text(
                **MessageBuilder.build_error_message("No sheet selected. Please use /start to select a sheet.")
            )
            return
            
        data = self._parse_object(update.message.text)
        if not data:
            await update.message.reply_text(
                **MessageBuilder.build_error_message(
                    "Invalid format. Please send data in the format:\n"
                    "field1: value1\nfield2: value2"
                )
            )
            return
            
        await self._handle_object_data(data, sheet_name, update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle column confirmation callbacks."""
        query = update.callback_query
        await query.answer()
        
        sheet_name = context.user_data.get('current_sheet')
        if not sheet_name:
            return
            
        if query.data.startswith("add_column:"):
            _, column = query.data.split(":", 2)[1:]
            self.sheets_service.add_columns(sheet_name, [column])
            
            # Remove the pending column and try to add data again
            state_data = self.get_state_data(context)
            if 'pending_columns' in state_data:
                state_data['pending_columns'].remove(column)
                
            if state_data.get('pending_data'):
                await self._handle_object_data(
                    state_data['pending_data'],
                    sheet_name,
                    update,
                    context
                )
                
        elif query.data.startswith("skip_column:"):
            _, column = query.data.split(":", 1)
            state_data = self.get_state_data(context)
            if 'pending_columns' in state_data:
                state_data['pending_columns'].remove(column)
                
            if state_data.get('pending_data'):
                await self._handle_object_data(
                    state_data['pending_data'],
                    sheet_name,
                    update,
                    context
                )
    
    def _parse_object(self, text: str) -> Optional[Dict[str, Any]]:
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
        except Exception:
            return None
    
    async def _handle_object_data(
        self,
        data: Dict[str, Any],
        sheet_name: str,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle parsed object data."""
        # Get current columns
        current_columns = self.sheets_service.get_columns(sheet_name)
        
        # Find new columns
        new_columns = [col for col in data.keys() if col not in current_columns]
        
        # If there are new columns, ask for confirmation
        if new_columns:
            state_data = self.get_state_data(context)
            if 'pending_columns' not in state_data:
                state_data['pending_columns'] = new_columns
                state_data['pending_data'] = data
            
            if not state_data['pending_columns']:
                # All columns have been handled
                self.sheets_service.append_row(sheet_name, data)
                await update.effective_message.reply_text(
                    **MessageBuilder.build_success_message("Data added successfully!")
                )
                self.clear_state_data(context)
                return
                
            # Ask about the next column
            column = state_data['pending_columns'][0]
            keyboard = KeyboardBuilder.build_column_confirmation_keyboard(sheet_name, column)
            
            await update.effective_message.reply_text(
                **MessageBuilder.build_new_column_confirmation(column, sheet_name, keyboard)
            )
            return
        
        # If no new columns, just add the data
        self.sheets_service.append_row(sheet_name, data)
        await update.effective_message.reply_text(
            **MessageBuilder.build_success_message("Data added successfully!")
        )
