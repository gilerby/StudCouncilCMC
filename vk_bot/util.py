import logging
from typing import Collection, Optional, Type

import numpy as np
from vkbottle.bot import Message, MessageEvent

from vk_bot.handlers import bot


class WrongObjectType(TypeError):
    def __init__(self, obj_name: str, obj_type: Type) -> None:
        super().__init__(f"Object {obj_name} has the wrong type {obj_type}")


def levenshtein_ratio(token1, token2):
    distances = np.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2

    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if token1[t1 - 1] == token2[t2 - 1]:
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]

                if a <= b and a <= c:
                    distances[t1][t2] = a + 1
                elif b <= a and b <= c:
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    return 1 - distances[len(token1)][len(token2)] / max(len(token1), len(token2))


def get_closest_str(comp_str, samples_arr: Collection[str], processor=None):
    max_ratio = 0
    closest_strs = []
    for sample in samples_arr:
        ratio = levenshtein_ratio(
            processor(sample) if processor else sample, comp_str
        )
        pair = (sample, ratio)
        if ratio > max_ratio:
            max_ratio = ratio
            closest_strs = [pair]
        elif ratio == max_ratio:
            closest_strs.append(pair)
    return closest_strs


def check_closest(comp_str, samples_arr: str | Collection[str], ratio=0.8):
    if isinstance(samples_arr, str):
        samples_arr = [samples_arr]

    closest_str = get_closest_str(comp_str, samples_arr)
    if len(closest_str) and closest_str[0][1] >= ratio:
        return True
    return False


async def edit_event_or_resend_message(event: MessageEvent, edit: bool, **kwargs):
    if edit:
        try:
            await event.edit_message(**kwargs)
            return event.conversation_message_id
        except Exception as err:
            logging.error(f"Error when editing a message: {err}")

    try:
        await bot.api.messages.delete(
            peer_id=event.peer_id,
            conversation_message_ids=event.conversation_message_id,
            delete_for_all=True,
        )
    except Exception as err:
        logging.error(f"Error deleting a message: {err}")

    return (await event.send_message(**kwargs)).conversation_message_id


async def answer(
    message_or_event: Optional[Message | MessageEvent],
    /,
    edit=True,
    dont_parse_links=True,
    **kwargs,
):
    kwargs.update({"dont_parse_links": dont_parse_links})

    if isinstance(message_or_event, Message):
        return (await message_or_event.answer(**kwargs)).conversation_message_id

    if isinstance(message_or_event, MessageEvent):
        return await edit_event_or_resend_message(message_or_event, edit, **kwargs)

    raise TypeError(
        f"message_or_event must be of type Message or MessageEvent, "
        f"but has type {type(message_or_event)}"
    )


def get_user_id_from_message_or_event(message_or_event: Message | MessageEvent):
    if isinstance(message_or_event, Message):
        return message_or_event.from_id
    elif isinstance(message_or_event, MessageEvent):
        return message_or_event.user_id
    raise WrongObjectType("message_or_event", type(message_or_event))
