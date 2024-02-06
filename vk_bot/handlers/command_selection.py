import traceback
from typing import Optional

from loguru import logger
from vkbottle.bot import Message, MessageEvent

from vk_bot.context_manager import ActiveState, FinalState, StateType
from vk_bot.util import check_closest

from . import PAYLOAD_ACTION, PAYLOAD_KEY, bot, context_manager


def get_command(message: Message) -> StateType:
    payload = message.get_payload_json()
    if not isinstance(payload, dict):
        payload = {}

    if payload.get(PAYLOAD_KEY.COMMAND) == PAYLOAD_ACTION.START_VOTING or check_closest(
        message.text.lower(), ["голос", "голосование", "vote", "voting"]
    ):
        return ActiveState.voting
    if payload.get(PAYLOAD_KEY.COMMAND) == PAYLOAD_ACTION.START or check_closest(
        message.text.lower(), ["начать", "привет", "start", "hello"]
    ):
        return ActiveState.welcome
    if check_closest(
        message.text.lower(),
        ["помогите", "помощь", "help", "мне нужна помощь", "поддержка", "контакты"],
    ):
        return ActiveState.help

    return FinalState.default


@context_manager.on_state(FinalState.default)
async def handle_message(message: Message) -> Optional[StateType]:
    return get_command(message)


@context_manager.on_state(FinalState.default)
async def handle_event(event: MessageEvent):
    try:
        await bot.api.messages.delete(
            peer_id=event.peer_id,
            cmids=[event.conversation_message_id],
            delete_for_all=True,
        )
    except Exception:
        logger.error(traceback.format_exc())


@context_manager.on_state(FinalState.command_selection)
async def process_command_selection(message: Message) -> StateType:
    return get_command(message)
