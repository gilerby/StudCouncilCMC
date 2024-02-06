from aiogram.fsm.context import FSMContext

from . import bot


async def delete_inline_message(storage:dict,state: FSMContext):
#Удаляем сообщения с прошлым голосованием
    if storage["last_inline_messages"] :
        for msg in storage["last_inline_messages"]:
            try:
                await bot.delete_message(chat_id = storage["user_id"],  message_id = msg)
            except:
                continue
    await state.update_data(last_inline_messages = [])