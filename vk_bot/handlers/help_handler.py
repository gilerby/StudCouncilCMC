from vkbottle.bot import Message

from vk_bot.config import SUPPORT_CONTACTS
from vk_bot.context_manager import ActiveState
from vk_bot.util import answer

from . import context_manager


@context_manager.on_state(ActiveState.help)
async def process_help(message: Message):
    await answer(
        message,
        message=(
            "❔ Если у Вас возникли вопросы или проблемы при работе с ботом, "
            f"пожалуйста, обратитесь в поддержку:\n\n{SUPPORT_CONTACTS}\n\n"
            "📝 Если у вас есть вопрос в Студенческий совет, задайте его в этом чате и ожидайте ответа."
        ),
    )
