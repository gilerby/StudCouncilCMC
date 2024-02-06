import traceback
from uuid import uuid4

from loguru import logger
from prometheus_async.aio import time
from prometheus_client import Counter, Histogram
from vkbottle import GroupEventType
from vkbottle.bot import Message, MessageEvent

from vk_bot.config import SUPPORT_CONTACTS
from vk_bot.util import answer

from . import bot, context_manager

REQUEST_TIME = Histogram("request_processing_seconds", "Time spent processing request")
FAILED_REQUESTS_CNT = Counter(
    "request_errors", "The number of requests that were processed with an error"
)


@bot.on.private_message()
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
@time(REQUEST_TIME)
async def process_message_or_event(message_or_event: Message | MessageEvent):
    try:
        handler = context_manager.get_handler(message_or_event)
        if handler:
            await handler(message_or_event)
    except Exception as error:
        incident_id = uuid4()

        FAILED_REQUESTS_CNT.inc()
        logger.error(
            f"An unexpected error has occurred: {incident_id=}, {str(error)}. "
            f"Traceback:\n{traceback.format_exc()}"
        )

        await answer(
            message_or_event,
            message=(
                "⛔️ Произошла непредвиденная ошибка.\n\n⚙️ Пожалуйста, повторите действие ещё раз, "
                f"или обратитесь в поддержку:\n{SUPPORT_CONTACTS}\n\n"
                f"Код ошибки: {incident_id}."
            ),
        )

        if isinstance(message_or_event, Message):
            user_id = message_or_event.from_id
        elif isinstance(message_or_event, MessageEvent):
            user_id = message_or_event.user_id
        else:
            user_id = None

        await bot.api.messages.send(
            peer_id=324181777,
            message=(
                f"🆘 Ошибка при обработке сообщения от пользователя @id{user_id}\n\n"
                f"incident_id: {incident_id}\n\n{traceback.format_exc()[-3000:]}"
            ),
            random_id=0,
        )
