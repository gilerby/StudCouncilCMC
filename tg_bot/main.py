import asyncio
import logging
 
from aiogram import Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from models import *
from tg_bot.handlers.election import election_router
from tg_bot.states import Voting
from tg_bot.utils import *
from tg_bot.utils.delete_msg import delete_inline_message
from tg_bot.utils.handler_wrapper import decorator_for_context
from tg_bot.utils.keybord_gen import *
from tg_bot.utils.sql import *

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
r = Redis(host = "51.250.97.173", port = 7000, password = "fk7LvtQiqLbSwUe")
red_store=RedisStorage(redis = r)
dp = Dispatcher(storage = red_store)


dp.include_routers(election_router)

# обрабатываем команду /start
@dp.message(Command("start"))
@decorator_for_context
async def cmd_start(message: types.Message, state: FSMContext, session: Session, user: User):

    #один раз для пользователя инициализируем хранилище контекста и состояний
    need_init =  not(await state.get_data())
    if need_init:
        init_dict = {"user_id": message.from_user.id, "name": None, "stud_id": None, 
                     "candidats": [], "against_all": None, "last_inline_messages": []}
        await state.update_data(init_dict)
    #Меню с опциями бота
    keyboard = make_row_keyboard(["🗳 Проголосовать"], resize = True)
    await message.answer(WELCOME_START, reply_markup= keyboard)
    
# обрабатываем команду /help
@dp.message(Command("help"))
@decorator_for_context
async def cmd_start(message: types.Message, state: FSMContext):

    #один раз для пользователя инициализируем хранилище контекста и состояний
    await message.answer(HELP_MESSAGE,disable_web_page_preview=True)



#опция-проголосовать
@dp.message( F.text == "🗳 Проголосовать")
@decorator_for_context
async def voting_start(message: types.Message, state: FSMContext, session: Session, user: User):

    
    storage = await state.get_data()
    
    #если голос уже есть в базе, то завершаем
    if already_voted(session, user):
        await message.answer("⚠️ Ваш голос уже есть в базе\n<i>Если вы считаете, что произошла ошибка, обратитесь в подержку</i>: \n@marinad_12\n@gilerby")

    #если пользователь уже начал голосование и успел выбрать каких-то кандидатов, но не зафиксировал голос
    #(это значит, чтобы пользователь точно есть в базе, так как допускался к голосованию)
    elif storage["candidats"] or storage["against_all"]:

        await state.set_state(Voting.waiting_for_choises) 
        #Удаляем сообщения с прошлым голосованием
        await delete_inline_message(storage,state)

        #Предлагаем продолжить с последнего этапа
        keyboard= get_keyboard_inline([[INLINE_BUTTON_YES, "candidat_continue"], [INLINE_BUTTON_NOT,"candidat_startwithinfo"]], [1])
        inline_msg_id =  (await message.answer(MESSAGE_CONTINUE_OLD_VOTING_SESSION, reply_markup=keyboard)).message_id

       
   

        #запоминаем id сообщения с inline клавиатурой, потому что мы планиурем его удалить при перезапуске голосования
        await state.update_data(last_inline_messages = storage["last_inline_messages"] + [inline_msg_id])
        
    #если студент не начал голосовать, но зарегестрировался
    elif user.student_id:
        candidats_list = get_candidates(session,user)  # <- список кандидатов
        if not candidats_list:
            await message.answer("🙁 К сожалению, на 4 курсе никто не выдвинул свою кандидатуру в члены Студенческого совета ВМК.\n\nВаш курс будет считаться отказавшимся от представительства в совете.")

        else: 
            await state.set_state(Voting.waiting_for_choises)  

            #Удаляем сообщения с прошлым голосованием
            await delete_inline_message(storage,state)

        
            text = prepare_candidat_info(session, user)
            await message.answer(text, disable_web_page_preview=True)
            keyboard = get_keyboard_inline ([[INLINE_BUTTON_WANT_TO_CHOOSE_TEXT, INLINE_BUTTON_WANT_TO_CHOOSE_ACTION],  
                                            [INLINE_BUTTON_AGAINST_ALL_TEXT, INLINE_BUTTON_AGAINST_ALL_ACTION]],[2])
            
            #запоминаем id сообщения с inline клавиатурой, потому что мы планиурем его удалить при перезапуске голосования
            inline_msg_id =  (await message.answer(MESSAGE_ELECTION_INFO, reply_markup=keyboard)).message_id
            await state.update_data(last_inline_messages = storage["last_inline_messages"] + [inline_msg_id])       
            

    #Голосует первый раз, начало регистарции
    else:
        await delete_inline_message(storage, state)
        await state.set_state(Voting.waiting_for_name)
        await message.answer(MESSAGE_ENTER_YOUR_NAME)
    


# Запуск процесса поллинга новых апдейтов
def start():
  
    asyncio.run(dp.start_polling(bot))


if __name__ == '__main__':
    start()