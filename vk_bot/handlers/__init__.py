import traceback
import types

from loguru import logger
from vkbottle import Bot

from vk_bot.config import VK_BOT_TOKEN

bot: Bot = Bot(VK_BOT_TOKEN)  # noqa

from vk_bot.context_manager import ContextManager  # noqa

context_manager: ContextManager = ContextManager()  # noqa

STORAGE_KEY = types.SimpleNamespace()
STORAGE_KEY.FULL_NAME = "full_name"
STORAGE_KEY.FIRST_NAME = "first_name"
STORAGE_KEY.STUDENT_ID = "student_id"
STORAGE_KEY.VOTES_FOR = "votes_for"
STORAGE_KEY.VOTE_AGAINST_ALL = "vote_against_all"
STORAGE_KEY.VOTING_MSG_IDS_TO_DELETE = "voting_msg_ids_to_delete"

PAYLOAD_KEY = types.SimpleNamespace()
PAYLOAD_KEY.ACTION = "action"
PAYLOAD_KEY.CANDIDATE_ID = "candidate_id"
PAYLOAD_KEY.VALUE = "value"
PAYLOAD_KEY.COMMAND = "command"

PAYLOAD_ACTION = types.SimpleNamespace()
PAYLOAD_ACTION.VOTE_FOR = "vote_for"
PAYLOAD_ACTION.VOTE_AGAINST_ALL = "vote_against_all"
PAYLOAD_ACTION.FINISH_VOTING = "finish_voting"
PAYLOAD_ACTION.CONFIRM_VOTING = "confirm_voting"
PAYLOAD_ACTION.START_VOTING = "start_voting"
PAYLOAD_ACTION.START = "start"

# from .admin_handlers import admin_commands_menu, delete_votes  # noqa
from .base_handler import process_message_or_event  # noqa
from .command_selection import process_command_selection  # noqa
from .help_handler import process_help  # noqa
from .registration import process_approve_personal_info  # noqa
from .registration import process_name_and_request_student_id  # noqa
from .registration import process_student_id_and_request_approve  # noqa
from .registration import request_name  # noqa
from .voting import process_vote  # noqa
from .voting import waiting_for_confirm_votes  # noqa
from .voting import confirm_votes, welcome_to_voting  # noqa
from .welcome import welcome  # noqa


async def undefined_error_handler(error: Exception):
    logger.error(
        f"An unexpected error has occurred: {str(error)}. "
        f"Traceback:\n{traceback.format_exc()}"
    )


def run_bot_polling():
    bot.error_handler.register_undefined_error_handler(undefined_error_handler)
    bot.run_forever()
