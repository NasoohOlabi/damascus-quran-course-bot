#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using nested ConversationHandlers.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from config.constants import (
    ADDING_MEMBER,
    ADDING_SELF,
    ADDING_STUDENT,
    AGE,
    CHILDREN,
    CURRENT_FEATURE,
    CURRENT_LEVEL,
    DESCRIBING_SELF,
    END,
    FEATURES,
    FEMALE,
    GENDER,
    MALE,
    NAME,
    PARENTS,
    SELECTING_ACTION,
    SELECTING_FEATURE,
    SELECTING_GENDER,
    SELECTING_LEVEL,
    SELF,
    SHOWING,
    START_OVER,
    STOPPING,
    TYPING,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Helper
def _name_switcher(level: str) -> tuple[str, str]:
    if level == PARENTS:
        return "Father", "Mother"
    return "Brother", "Sister"


# Top level conversation callbacks
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select an action: Adding parent/child, yourself, student or show data."""
    text = (
        "You may choose to add a family member, yourself, a student, show the gathered data, or end the "
        "conversation. To abort, simply type /stop."
    )

    buttons = [
        [
            InlineKeyboardButton(
                text="Add family member", callback_data=str(ADDING_MEMBER)
            ),
            InlineKeyboardButton(text="Add yourself", callback_data=str(ADDING_SELF)),
        ],
        [
            InlineKeyboardButton(text="Add student", callback_data=str(ADDING_STUDENT)),
            InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
        ],
        [
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we're starting over we don't need to send a new message
    if context.user_data.get(START_OVER):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(
            "Hi, I'm Family Bot and I'm here to help you gather information about your family."
        )
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_ACTION


async def adding_self(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Add information about yourself."""
    context.user_data[CURRENT_LEVEL] = SELF
    text = "Okay, please tell me about yourself."
    button = InlineKeyboardButton(text="Add info", callback_data=str(MALE))
    keyboard = InlineKeyboardMarkup.from_button(button)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return DESCRIBING_SELF


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Pretty print gathered data."""

    def pretty_print(data: dict[str, Any], level: str) -> str:
        people = data.get(level)
        if not people:
            return "\nNo information yet."

        return_str = ""
        if level == SELF:
            for person in data[level]:
                return_str += (
                    f"\nName: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"
                )
        elif level == "students":
            # for student in data[level]:
            #     return_str += (
            #         f"\nStudent: {student.get(STUDENT_FIRSTNAME, '-')} {student.get(STUDENT_MIDDLENAME, '-')} "
            #         f"{student.get(STUDENT_LASTNAME, '-')}, Age: {student.get(STUDENT_AGE, '-')}, "
            #         f"Group: {student.get(STUDENT_GROUP, '-')}"
            #     )
            #     if student.get(STUDENT_NOTES):
            #         return_str += f"\n  Notes: {student.get(STUDENT_NOTES, '-')}"
            pass
        else:
            male, female = _name_switcher(level)

            for person in data[level]:
                gender = female if person[GENDER] == FEMALE else male
                return_str += f"\n{gender}: Name: {person.get(NAME, '-')}, Age: {person.get(AGE, '-')}"
        return return_str

    user_data = context.user_data
    text = f"Yourself:{pretty_print(user_data, SELF)}"
    text += f"\n\nParents:{pretty_print(user_data, PARENTS)}"
    text += f"\n\nChildren:{pretty_print(user_data, CHILDREN)}"
    text += f"\n\nStudents:{pretty_print(user_data, 'students')}"

    buttons = [[InlineKeyboardButton(text="Back", callback_data=str(END))]]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    user_data[START_OVER] = True

    return SHOWING


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    await update.message.reply_text("Okay, bye.")

    return END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)

    return END


# Second level conversation callbacks
async def select_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add a parent or a child."""
    text = "You may add a parent or a child. Also you can show the gathered data or go back."
    buttons = [
        [
            InlineKeyboardButton(text="Add parent", callback_data=str(PARENTS)),
            InlineKeyboardButton(text="Add child", callback_data=str(CHILDREN)),
        ],
        [
            InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Back", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_LEVEL


async def select_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Choose to add mother or father."""
    level = update.callback_query.data
    context.user_data[CURRENT_LEVEL] = level

    text = "Please choose, whom to add."

    male, female = _name_switcher(level)

    buttons = [
        [
            InlineKeyboardButton(text=f"Add {male}", callback_data=str(MALE)),
            InlineKeyboardButton(text=f"Add {female}", callback_data=str(FEMALE)),
        ],
        [
            InlineKeyboardButton(text="Show data", callback_data=str(SHOWING)),
            InlineKeyboardButton(text="Back", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)

    return SELECTING_GENDER


async def end_second_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Return to top level conversation."""
    context.user_data[START_OVER] = True
    await start(update, context)

    return END


# Third level callbacks
async def select_feature(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Select a feature to update for the person."""
    buttons = [
        [
            InlineKeyboardButton(text="Name", callback_data=str(NAME)),
            InlineKeyboardButton(text="Age", callback_data=str(AGE)),
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # If we collect features for a new person, clear the cache and save the gender
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {GENDER: update.callback_query.data}
        text = "Please select a feature to update."

        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    # But after we do that, we need to send a new message
    else:
        text = "Got it! Please select a feature to update."
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE


async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = "Okay, tell me."

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    return TYPING


async def save_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Save input for feature and return to feature selection."""
    user_data = context.user_data
    user_data[FEATURES][user_data[CURRENT_FEATURE]] = update.message.text

    user_data[START_OVER] = True

    return await select_feature(update, context)


async def end_describing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End gathering of features and return to parent conversation."""
    user_data = context.user_data
    level = user_data[CURRENT_LEVEL]
    if not user_data.get(level):
        user_data[level] = []
    user_data[level].append(user_data[FEATURES])

    # Print upper level menu
    if level == SELF:
        user_data[START_OVER] = True
        await start(update, context)
    else:
        await select_level(update, context)

    return END


async def stop_nested(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Completely end conversation from within nested conversation."""
    await update.message.reply_text("Okay, bye.")

    return STOPPING
