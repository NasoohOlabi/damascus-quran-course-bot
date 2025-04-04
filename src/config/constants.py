from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# State definitions for top level conversation
SELECTING_ACTION, ADDING_MEMBER, ADDING_SELF, DESCRIBING_SELF = map(chr, range(4))
# State definitions for second level conversation
SELECTING_LEVEL, SELECTING_GENDER = map(chr, range(5, 7))
# State definitions for descriptions conversation
SELECTING_FEATURE, TYPING = map(chr, range(7, 9))
# Meta states
STOPPING, SHOWING = map(chr, range(9, 11))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Different constants for this example
(
    PARENTS,
    CHILDREN,
    SELF,
    GENDER,
    MALE,
    FEMALE,
    AGE,
    NAME,
    START_OVER,
    FEATURES,
    CURRENT_FEATURE,
    CURRENT_LEVEL,
) = map(chr, range(11, 23))


# Student related constants
(
    STUDENT_FIRSTNAME,
    STUDENT_MIDDLENAME,
    STUDENT_LASTNAME,
    STUDENT_AGE,
    STUDENT_GROUP,
    STUDENT_NOTES,
) = map(chr, range(23, 29))
