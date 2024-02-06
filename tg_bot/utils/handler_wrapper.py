import inspect
import traceback
from aiogram import types
from aiogram.fsm.context import FSMContext

from models import Session
from tg_bot.utils.sql import get_or_create_user,prepare_candidat_info
from tg_bot.utils.delete_msg import delete_inline_message
from tg_bot.utils.keybord_gen import *
from tg_bot.states import Voting
from . import *
import logging


def decorator_for_context(function_to_decorate):
    async  def a_wrapper_accepting_arguments(mess, state: FSMContext):

        
        flag = mutex.get_flag(mess.from_user.id)
        if not flag:
            message = mess if isinstance(mess, types.Message) else mess.message
            await bot.send_chat_action(message.chat.id, 'typing')
            try:
                parameterized_func = function_to_decorate
                handler_args = inspect.signature(function_to_decorate).parameters.keys()
                if 'session' in handler_args:
                    with Session() as session:
                        user = get_or_create_user(session, mess.from_user.id)
                        await parameterized_func(mess, state,session, user)
                else:
                    await parameterized_func(mess,state)
                
        
            except:
                logging.error(traceback.format_exc())
                storage = await state.get_data()
                init_dict = {"user_id": mess.from_user.id, "name": None, "stud_id": None, "candidats": [], "against_all": None, "last_inline_messages": []}
                await state.set_data(init_dict) 
                keyboard = make_row_keyboard(["🗳 Проголосовать"], resize = True)
                await message.answer(ERROR_MESSAGE, reply_markup = keyboard)  
                await delete_inline_message(storage,state)
                await state.set_state(state = None)                 
        
            mutex.free_lock(mess.from_user.id)


                

    return a_wrapper_accepting_arguments