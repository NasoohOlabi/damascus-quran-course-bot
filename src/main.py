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

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.bot import (
    ADDING_MEMBER,
    ADDING_SELF,
    CHILDREN,
    DESCRIBING_SELF,
    END,
    FEMALE,
    MALE,
    PARENTS,
    SELECTING_ACTION,
    SELECTING_FEATURE,
    SELECTING_GENDER,
    SELECTING_LEVEL,
    SHOWING,
    STOPPING,
    TYPING,
    adding_self,
    ask_for_input,
    end,
    end_describing,
    end_second_level,
    save_input,
    select_feature,
    select_gender,
    select_level,
    show_data,
    start,
    stop,
    stop_nested,
)
from conversations.student_conversation import (
    studentsConversationHandler,
)
from src.load_config import load_config
from src.utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)


def main() -> None:
    """Run the bot."""
    logger.info("Initializing bot application")
    config = load_config()

    application = Application.builder().token(config.TOKEN).build()

    # Set up third level ConversationHandler (collecting features)
    description_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                select_feature, pattern="^" + str(MALE) + "$|^" + str(FEMALE) + "$"
            )
        ],
        states={
            SELECTING_FEATURE: [
                CallbackQueryHandler(ask_for_input, pattern="^(?!" + str(END) + ").*$")
            ],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_input)],
        },
        fallbacks=[
            CallbackQueryHandler(end_describing, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # Return to second level menu
            END: SELECTING_LEVEL,
            # End conversation altogether
            STOPPING: STOPPING,
        },
    )

    # Set up second level ConversationHandler (adding a person)
    add_member_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_level, pattern="^" + str(ADDING_MEMBER) + "$")
        ],
        states={
            SELECTING_LEVEL: [
                CallbackQueryHandler(select_gender, pattern=f"^{PARENTS}$|^{CHILDREN}$")
            ],
            SELECTING_GENDER: [description_conv],
        },
        fallbacks=[
            CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
            CallbackQueryHandler(end_second_level, pattern="^" + str(END) + "$"),
            CommandHandler("stop", stop_nested),
        ],
        map_to_parent={
            # After showing data return to top level menu
            SHOWING: SHOWING,
            # Return to top level menu
            END: SELECTING_ACTION,
            # End conversation altogether
            STOPPING: END,
        },
    )

    # Set up top level ConversationHandler (selecting action)
    # Because the states of the third level conversation map to the ones of the second level
    # conversation, we need to make sure the top level conversation can also handle them
    selection_handlers = [
        add_member_conv,
        studentsConversationHandler,
        CallbackQueryHandler(show_data, pattern="^" + str(SHOWING) + "$"),
        CallbackQueryHandler(adding_self, pattern="^" + str(ADDING_SELF) + "$"),
        CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SHOWING: [CallbackQueryHandler(start, pattern="^" + str(END) + "$")],
            SELECTING_ACTION: selection_handlers,  # type: ignore[dict-item]
            SELECTING_LEVEL: selection_handlers,  # type: ignore[dict-item]
            DESCRIBING_SELF: [description_conv],
            STOPPING: [CommandHandler("start", start)],
            # TEACHERS_MGMT: [CallbackQueryHandler(handle_teacher_management, pattern="^" + str(TEACHERS_MGMT) + "$")],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Shutdown requested via keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        raise
