from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config.constants import (
    CURRENT_FEATURE,
    END,
    FEATURES,
    SELECTING_ACTION,
    SELECTING_FEATURE,
    START_OVER,
    STOPPING,
    STUDENT_AGE,
    STUDENT_FIRSTNAME,
    STUDENT_GROUP,
    STUDENT_LASTNAME,
    STUDENT_MIDDLENAME,
    STUDENT_NOTES,
    TYPING,
)
from models.student import Student
from src.bot.bot import save_input, start, stop_nested


# Student conversation callbacks
async def adding_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Add a new student to the system."""
    text = "Please provide the following information about the student."

    buttons = [
        [
            InlineKeyboardButton(
                text="First Name", callback_data=str(STUDENT_FIRSTNAME)
            ),
            InlineKeyboardButton(
                text="Middle Name", callback_data=str(STUDENT_MIDDLENAME)
            ),
        ],
        [
            InlineKeyboardButton(text="Last Name", callback_data=str(STUDENT_LASTNAME)),
            InlineKeyboardButton(text="Age", callback_data=str(STUDENT_AGE)),
        ],
        [
            InlineKeyboardButton(text="Group", callback_data=str(STUDENT_GROUP)),
            InlineKeyboardButton(text="Notes", callback_data=str(STUDENT_NOTES)),
        ],
        [
            InlineKeyboardButton(text="Done", callback_data=str(END)),
            InlineKeyboardButton(text="Cancel", callback_data=str(STOPPING)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    # Initialize student data structure if it doesn't exist
    if not context.user_data.get("students"):
        context.user_data["students"] = []

    # Initialize current student features
    if not context.user_data.get(START_OVER):
        context.user_data[FEATURES] = {}
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE


async def select_student_feature(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str:
    """Select a feature to update for the student."""
    buttons = [
        [
            InlineKeyboardButton(
                text="First Name", callback_data=str(STUDENT_FIRSTNAME)
            ),
            InlineKeyboardButton(
                text="Middle Name", callback_data=str(STUDENT_MIDDLENAME)
            ),
        ],
        [
            InlineKeyboardButton(text="Last Name", callback_data=str(STUDENT_LASTNAME)),
            InlineKeyboardButton(text="Age", callback_data=str(STUDENT_AGE)),
        ],
        [
            InlineKeyboardButton(text="Group", callback_data=str(STUDENT_GROUP)),
            InlineKeyboardButton(text="Notes", callback_data=str(STUDENT_NOTES)),
        ],
        [
            InlineKeyboardButton(text="Done", callback_data=str(END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    if not context.user_data.get(START_OVER):
        text = "Please select a student feature to update."
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    else:
        text = "Got it! Please select another feature to update or press Done when finished."
        await update.message.reply_text(text=text, reply_markup=keyboard)

    context.user_data[START_OVER] = False
    return SELECTING_FEATURE


async def save_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save student information and return to main menu."""
    user_data = context.user_data
    features = user_data.get(FEATURES, {})

    # Only save if we have at least first name and last name
    if features.get(STUDENT_FIRSTNAME) and features.get(STUDENT_LASTNAME):
        if not user_data.get("students"):
            user_data["students"] = []

        user_data["students"].append(features.copy())

        # Create a Student object (for future use with save logic)
        student_dict = {
            "firstname": features.get(STUDENT_FIRSTNAME, ""),
            "middlename": features.get(STUDENT_MIDDLENAME, ""),
            "lastname": features.get(STUDENT_LASTNAME, ""),
            "age": int(features.get(STUDENT_AGE, 0))
            if features.get(STUDENT_AGE, "").isdigit()
            else 0,
            "group": features.get(STUDENT_GROUP, ""),
            "notes": features.get(STUDENT_NOTES, ""),
        }

        student = Student.from_dict(student_dict)
        # TODO: Implement actual saving of student data
        # student.save()

        await update.callback_query.answer("Student information saved!")
    else:
        await update.callback_query.answer(
            "Student needs at least first and last name!"
        )

    user_data[START_OVER] = True
    await start(update, context)

    return END


async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Prompt user to input data for selected feature."""
    context.user_data[CURRENT_FEATURE] = update.callback_query.data
    text = "Okay, tell me."

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(text=text)

    return TYPING


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End conversation from InlineKeyboardButton."""
    await update.callback_query.answer()

    text = "See you around!"
    await update.callback_query.edit_message_text(text=text)

    return END


studentsConversationHandler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(adding_student, pattern="^" + str(STUDENT_FIRSTNAME) + "$")
    ],
    states={
        SELECTING_FEATURE: [
            CallbackQueryHandler(
                ask_for_input,
                pattern="^(?!" + str(END) + ")(?!" + str(STOPPING) + ").*$",
            ),
            CallbackQueryHandler(save_student, pattern="^" + str(END) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(STOPPING) + "$"),
        ],
        TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
    },
    fallbacks=[
        CommandHandler("stop", stop_nested),
    ],
    map_to_parent={
        # Return to top level menu
        END: SELECTING_ACTION,
        # End conversation altogether
        STOPPING: END,
    },
)
