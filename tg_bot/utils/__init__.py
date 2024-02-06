from aiogram import Bot

from tg_bot.utils.user_context import mutex

mutex = mutex()
bot = Bot(token="6585128636:AAFFPxC1vNvae6dZZjcbYsOtw1_MCTIXP8U",  parse_mode="HTML")
max_can = 4
INLINE_BUTTON_STEP_BACK = 'Назад'
INLINE_BUTTON_AGAINST_ALL_TEXT = "Против всех"
INLINE_BUTTON_AGAINST_ALL_ACTION = "candidat_disagree" 
INLINE_BUTTON_WANT_TO_CHOOSE_TEXT = "Начать"
INLINE_BUTTON_WANT_TO_CHOOSE_ACTION = "candidat_agree"
INLINE_BUTTON_AGAINST_ALL_CONFIRM_ACTION = "candidat_refuse"
INLINE_BUTTON_TO_VOTE = "Завершить"
INLINE_BUTTON_CANCEL = "Отмена"
INLINE_BUTTON_YES = "Да"
INLINE_BUTTON_NOT = "Нет"

MESSAGE_ENTER_YOUR_NAME = "Укажите свою фамилию, имя и отчество(при наличии)"
MESSAGE_ENTER_YOUR_STUD_ID = "Укажите номер Вашего студенческого билета"
MESSAGE_ELECTION_INFO = "📋 Вы можете выбрать до 3 кандидатов или проголсоовать за отказ представительства курса в Студенческом совете ВМК"
MESSAGE_AGAINST_ALL_ENSURE = "⁉️ Вы уверены, что хотите проголосовать за отказ от представительства курса в Студенческом совете"
MESSAGE_AGAINST_ALL_FINISH = "Вы проголосовали за отказ от представительства Вашего курса в СС ВМК"
MESSAGE_VOTER_INLINE_BUTTON_NOTT_IN_DATABASE = f"Хмммммм, не видим вас в списках. \
                                                \nПроверьте корректность указанных вами данных и повторите попытку ввода. \
                                                \nЕсли это не помогло, обратитесь в поддержку: \n@marinad_12\n@gilerby\n\n\n{MESSAGE_ENTER_YOUR_NAME}"

MESSAGE_VOTING_FINISH = "Ваш голос учтён!\nЭто Ваш ID избирателя [].....\nс помощью него вы сможете проверить, что Ваш голос учтен правильно.\n\n\nСпасибо за участие!"
MESSAGE_CONTINUE_OLD_VOTING_SESSION = "🤔 Похоже Вы уже начали голосовать, хотите продолжить?"

KEYBOARD_CORECT_FOR_REG = 'Верно'
KEYBOARD_INCORECT_FOR_REG = 'Исправить'
HELP_MESSAGE ='При возникновении проблем с работой бота обращайтесь к:\n@marinad_12\n@gilerby \
\nПри возникновении вопросов по выборам обращайтесь в официальную группу <a href="https://vk.com/cmcsovet">Студсовета ВМК</a> '

WELCOME_START = "👋 Здравствуйте!\nЕсли вы студент ВМК, вы можете проголосовать на выборах в Студенческий совет ВМК."
ERROR_MESSAGE = "⛔️ Упс, что-то пошло не так, попробуйте еще раз\n\n \
\nЕсли проблема сохрнаится, попробуйте воспользоваться ботом ВК или обратитесь в поддержку: \n@marinad_12\n@gilerby"