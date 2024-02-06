import os


def _parse_int_array(array: str | None):
    if not isinstance(array, str):
        return []
    return [*map(lambda number: int(number.strip()), array.split(","))]


__ALLOWED_LOG_LEVELS = [
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
]


VK_BOT_TOKEN = os.getenv("VK_BOT_TOKEN")
assert VK_BOT_TOKEN

VK_ADMIN_IDS = _parse_int_array(os.getenv("VK_ADMIN_IDS"))

USER_CONTEXT_FILE = ".user_context"

LOG_LEVEL = os.getenv("VK_LOG_LEVEL", "INFO")
assert LOG_LEVEL in __ALLOWED_LOG_LEVELS

SUPPORT_CONTACTS = os.getenv("VK_SUPPORT_CONTACTS")
assert SUPPORT_CONTACTS
SUPPORT_CONTACTS = SUPPORT_CONTACTS.replace("\\n", "\n")

MAX_VOTES_NUMBER = int(os.getenv("MAX_VOTES_NUMBER", 4))
