from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from models import *
from tg_bot.states import Voting
from tg_bot.utils import *
from tg_bot.utils.delete_msg import delete_inline_message
from tg_bot.utils.handler_wrapper import decorator_for_context
from tg_bot.utils.keybord_gen import *
from tg_bot.utils.sql import *

election_router = Router()

#global list of can


# Имя введено, уточняет, правильно ли
@election_router.message(Voting.waiting_for_name, F.text)  
@decorator_for_context
async def wait_for_name(message: types.Message, state: FSMContext):
    
    await state.set_state(Voting.checking_the_name)
    await state.update_data(name = message.text)
    keyboard = make_row_keyboard([KEYBOARD_CORECT_FOR_REG, KEYBOARD_INCORECT_FOR_REG])
    await message.answer(f"Вас зовут: \n\n{message.text}\n\nВерно?", reply_markup=keyboard)


# Имя введено неправильно, снова запрашивает имя
@election_router.message(Voting.checking_the_name, F.text == KEYBOARD_INCORECT_FOR_REG)  
@decorator_for_context
async def correct_the_name(message: types.Message, state: FSMContext): 
    await state.set_state(Voting.waiting_for_name)
    await state.update_data(name = '')
    await message.answer(MESSAGE_ENTER_YOUR_NAME)
   

# Имя введено правильно, запрашивает студак
@election_router.message(Voting.checking_the_name, F.text == KEYBOARD_CORECT_FOR_REG)  
@decorator_for_context
async def get_the_Stud_id(message: types.Message, state: FSMContext):
    await state.set_state(Voting.waiting_for_studid)
    await message.answer(MESSAGE_ENTER_YOUR_STUD_ID)



# Студак введен, уточянет правильно ли
@election_router.message(Voting.waiting_for_studid, F.text)  
@decorator_for_context
async def wait_for_studID(message: types.Message, state: FSMContext):
    await state.set_state(Voting.checking_the_studid)
    await state.update_data(stud_id = message.text)
    keyboard = make_row_keyboard([KEYBOARD_CORECT_FOR_REG, KEYBOARD_INCORECT_FOR_REG])
    await message.answer(f"Номер Вашего студенческого билета: \n\n{message.text}\n\nВерно?",  reply_markup=keyboard)
    

# Студак неправильный, просим еще раз
@election_router.message(Voting.checking_the_studid, F.text == KEYBOARD_INCORECT_FOR_REG)  
@decorator_for_context
async def correct_the_studID(message: types.Message, state: FSMContext):
    await state.set_state(Voting.waiting_for_studid) 
    await state.update_data(stud_id = '')
    await message.answer(MESSAGE_ENTER_YOUR_STUD_ID)
 
#Получили студак и ФИО, ищем студента в списках
@election_router.message(Voting.checking_the_studid, F.text == KEYBOARD_CORECT_FOR_REG)  
@decorator_for_context
async def get_the_name(message: types.Message, state: FSMContext, session: Session, user: User):   

    #обращение к базе
    storage = await state.get_data() 
    bd_response = name_in_studlist(session, storage)
    

    
    #Если пользователь есть в списке студентов факультета, то разрешаем 
    if bd_response:
        add_studID(session,storage,user)
        candidats_list = get_candidates(session,user)  # <- список кандидатов
        if not candidats_list:
            await message.answer("🙁 К сожалению, на 4 курсе никто не выдвинул свою кандидатуру в члены Студенческого совета ВМК.\n\nВаш курс будет считаться отказавшимся от представительства в совете.")
            await state.set_state(None)
        else:
            if already_voted(session, user):
                await message.answer("⚠️ Ваш голос уже есть в базе\n<i>Если вы считаете, что произошла ошибка, обратитесь в подержку</i>: \n@marinad_12\n@gilerby")
            else:
                await state.set_state(Voting.waiting_for_choises) 
                    
                #Удаляем сообщения с прошлым голосованием
                await delete_inline_message(storage, state)


                text = prepare_candidat_info(session, user)
                await message.answer(text, disable_web_page_preview=True)
                keyboard = get_keyboard_inline([[INLINE_BUTTON_WANT_TO_CHOOSE_TEXT, INLINE_BUTTON_WANT_TO_CHOOSE_ACTION], 
                                                [INLINE_BUTTON_AGAINST_ALL_TEXT, INLINE_BUTTON_AGAINST_ALL_ACTION]],[2])
                
                inline_msg_id =  (await message.answer(MESSAGE_ELECTION_INFO, reply_markup=keyboard)).message_id


                #запоминаем id сообщения с inline клавиатурой, потому что мы планиурем его удалить при перезапуске голосования
                await state.update_data(last_inline_messages = storage["last_inline_messages"] + [inline_msg_id])       
                
    #Иначе сообщение поддержки и приглашение на повторную регистрацию
    else: 
        await state.set_state(Voting.waiting_for_name)
        storage['STUD_ID'] = ''
        storage['NAME']    = ''
        await message.answer(MESSAGE_VOTER_INLINE_BUTTON_NOTT_IN_DATABASE)
            


@election_router.callback_query(Voting.waiting_for_choises, F.data.startswith("candidat") )
@decorator_for_context
async def callbacks_votecandidat(callback: types.CallbackQuery,  state: FSMContext,session: Session, user: User):
    candidat_index = callback.data.split("_")[1]   # <- текущая команда
    candidats_list = get_candidates(session,user)  # <- список кандидатов
    storage = await state.get_data()

    match candidat_index:

        #Это начало. >--Против всех/выбрать кандидатов--<
        case "start":
            
            await state.update_data(against_all = False, candidats = [])
            keyboard = get_keyboard_inline([[INLINE_BUTTON_WANT_TO_CHOOSE_TEXT, INLINE_BUTTON_WANT_TO_CHOOSE_ACTION], 
                                            [INLINE_BUTTON_AGAINST_ALL_TEXT, INLINE_BUTTON_AGAINST_ALL_ACTION]],[2])
            
            await callback.message.edit_text(MESSAGE_ELECTION_INFO,  reply_markup=keyboard)

        case "startwithinfo":
            await state.update_data(against_all = False, candidats = [])
            await delete_inline_message(storage, state)
            text = prepare_candidat_info(session, user)
            await callback.message.answer(text, disable_web_page_preview=True)
            keyboard = get_keyboard_inline([[INLINE_BUTTON_WANT_TO_CHOOSE_TEXT, INLINE_BUTTON_WANT_TO_CHOOSE_ACTION], 
                                            [INLINE_BUTTON_AGAINST_ALL_TEXT, INLINE_BUTTON_AGAINST_ALL_ACTION]],[2])
            
            inline_msg_id = (await callback.message.answer(MESSAGE_ELECTION_INFO,  reply_markup=keyboard)).message_id

            await state.update_data(last_inline_messages = storage["last_inline_messages"] + [inline_msg_id])


        #Решили не против всех. >--Список кандидатов/назад--<
        case "agree":
            await state.update_data(candidats = [])
            keyboard = get_keyboard_inline([[x.name, f"candidat_{x.id}"] for x in candidats_list] 
                                          +[[INLINE_BUTTON_STEP_BACK,"candidat_start"]], [1])
            
            await callback.message.edit_text("⬇️ Выберите кандидатов", reply_markup = keyboard)

        #Решили против всех.  >--Проголосовать/отмена--<
        case "disagree": 
            await state.update_data(against_all = True)
            keyboard=get_keyboard_inline([[INLINE_BUTTON_AGAINST_ALL_TEXT, "candidat_finish"],
                                          [INLINE_BUTTON_CANCEL, "candidat_start"]],[2])
            
            await callback.message.edit_text(MESSAGE_AGAINST_ALL_ENSURE,reply_markup=keyboard)

        
        #Решили выбрать меньше max(кандидатов).  >--Проголосовать/отмена--<
        case "stop":
            
            keyboard = get_keyboard_inline([[INLINE_BUTTON_TO_VOTE, "candidat_finish"],[INLINE_BUTTON_CANCEL, 'candidat_notfinish']], [2])
            text = "Вы выбрали кандидатов:\n\n📌" \
                   +"\n\n📌 ".join(map (lambda vote: vote.name, get_id_from_candidat(storage["candidats"], candidats_list)) ) \
                   + "\n\n\n✅ Подтвержаете свой выбор?" 
            await callback.message.edit_text(text, reply_markup = keyboard)
         
        #Завершаем голосование при достижении max(каднидаты), заносим в базу
        case "finish":

            # Проверим, нет ли голоса уже в базе
            if already_voted(session, user):
                await callback.message.edit_text("⚠️ Ваш голос уже есть базе!\n<i>Если вы считаете, что произошла ошибка, обратитесь в подержку</i>: \n@marinad_12\n@gilerby")

            else:
                msg = vote_to_database(session, storage,user)
                await callback.message.edit_text(msg)

            #очищаем контекст    
            await state.clear()

        #Решили не подтверждать выбор max(кандидатов)>--candidatlist/stop/back--<
        case  "notfinish":

            keyboard = get_keyboard_inline(kb := [[x.name, f"candidat_{x.id}"] for x in candidats_list  if x.id not in storage["candidats"]] \
                                          + [[INLINE_BUTTON_TO_VOTE, "candidat_stop"],[INLINE_BUTTON_CANCEL, "candidat_back"]], [1 ]*(len(kb)-2) + [2]) 
            text = "Вы выбрали кандидатов:\n\n📌 "+"\n\n📌 ".join(map (lambda vote: vote.name, get_id_from_candidat(storage["candidats"], candidats_list)) )
            await callback.message.edit_text(text, reply_markup = keyboard)
        
        #отмена последнего выбранного кандидата
        case "back":

            if storage["candidats"]:
                storage["candidats"].pop()

            await state.update_data(candidats = storage["candidats"])
            
            #Если не выбрано ни одного кандидита, то уже не предлагаем кнопку назад >--candidat list/back--<
            if len(storage["candidats"])  == 0 :
                keyboard = get_keyboard_inline([[x.name,f"candidat_{x.id}"] for x in candidats_list] +[["Назад","candidat_start"]], [1])
                
                await callback.message.edit_text("⬇️ Выберите кандидатов",reply_markup = keyboard)         
            #>--candidatlist/stop/back--<
            else:
                keyboard = get_keyboard_inline(kb := [[x.name, f"candidat_{x.id}"] for x in candidats_list  if x.id not in storage["candidats"]] \
                                             + [[INLINE_BUTTON_TO_VOTE, "candidat_stop"],[INLINE_BUTTON_STEP_BACK, "candidat_back"]], [1 ]*(len(kb)-2) + [2])
                await callback.message.edit_text("Вы выбрали кандидатов:\n\n📌 "+"\n\n📌 ".join(map (lambda vote: vote.name, get_id_from_candidat(storage["candidats"], candidats_list)) ), reply_markup = keyboard)

        #выбор кандидата
        case _:
            #если мы продолжаем голосование с какого-то этапа, то нам нужно просто отобразить статус
            flag = True if candidat_index == "continue" or len(storage["candidats"]) == min (max_can,len(candidats_list)) else False
            print(flag)
            #Если пользователь хотел проголосовать против всех 
            if flag and storage["against_all"]:
                keyboard=get_keyboard_inline([[INLINE_BUTTON_AGAINST_ALL_TEXT, "candidat_finish"],
                                          [INLINE_BUTTON_CANCEL, "candidat_start"]],[2])
                await callback.message.edit_text(MESSAGE_AGAINST_ALL_ENSURE,reply_markup=keyboard)

            elif candidat_index not in list(map(str,storage["candidats"])):
                print(candidat_index)
                #Вписываем выбранного кандидата
                if not flag:
                   storage = await state.update_data(candidats = storage["candidats"] + [int(candidat_index)]) 

                #достигнут максимум голосов >--back/finish--<
                if len(storage["candidats"]) == min (max_can,len(candidats_list)) :
                    
                    keyboard = get_keyboard_inline([[INLINE_BUTTON_TO_VOTE, "candidat_finish"],[INLINE_BUTTON_CANCEL, 'candidat_back']], [2])
                    check = "\n\n\n✅ Подтвержаете свой выбор?" 
            
                #>--Список кандидатов/stop/back--<
                elif len(storage["candidats"]) < min (max_can,len(candidats_list)) :
                    print('ass')
                    keyboard = get_keyboard_inline(kb := [[x.name, f"candidat_{x.id}"] for x in candidats_list  if x.id not in storage["candidats"]] \
                            + [[INLINE_BUTTON_TO_VOTE, "candidat_stop"],[INLINE_BUTTON_STEP_BACK, "candidat_back"]], [1 ]*(len(kb)-2) + [2] )
                    check = ""



                text = "Вы выбрали кандидатов:\n\n📌 "+"\n\n📌 ".join(map (lambda vote: vote.name,  get_id_from_candidat(storage["candidats"], candidats_list)) ) + check
            
                await callback.message.edit_text(text, reply_markup= keyboard)
                

            
                
    




