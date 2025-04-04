from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from telegram import Update
from telegram.ext import ContextTypes


class State(ABC):
    """Base abstract class for all states in the state machine."""
    
    def __init__(self):
        self.next_state: Optional['State'] = None
    
    @abstractmethod
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages."""
        pass
    
    @abstractmethod
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries."""
        pass
    
    def get_next_state(self) -> Optional['State']:
        """Get the next state to transition to."""
        return self.next_state
    
    def reset_next_state(self) -> None:
        """Reset the next state."""
        self.next_state = None
    
    def get_state_data(self, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """Get state-specific data from user_data."""
        if 'state_data' not in context.user_data:
            context.user_data['state_data'] = {}
        return context.user_data['state_data']
    
    def clear_state_data(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear state-specific data."""
        if 'state_data' in context.user_data:
            context.user_data['state_data'] = {}