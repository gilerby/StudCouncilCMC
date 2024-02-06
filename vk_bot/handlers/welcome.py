from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message, MessageEvent

from vk_bot.context_manager import ActiveState, FinalState, StateType
from vk_bot.util import answer

from . import PAYLOAD_ACTION, PAYLOAD_KEY, context_manager


@context_manager.on_state(ActiveState.welcome)
async def welcome(message_or_event: Message | MessageEvent) -> StateType:
    keyboard = Keyboard(inline=False, one_time=True).add(
        Text("🗳️ Голосование", {PAYLOAD_KEY.COMMAND: PAYLOAD_ACTION.START_VOTING}),
        KeyboardButtonColor.SECONDARY,
    )

    await answer(
        message_or_event,
        message="👋 Здравствуйте!\nЕсли вы студент ВМК, вы можете проголосовать на выборах в Студенческий совет ВМК.",
        keyboard=keyboard.get_json(),
    )
    return FinalState.command_selection
