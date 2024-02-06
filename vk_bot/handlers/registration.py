from sqlalchemy.orm import Session
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message, MessageEvent

from models import Student, User
from vk_bot.config import SUPPORT_CONTACTS
from vk_bot.context_manager import (
    ActiveState,
    FinalState,
    StorageType,
)
from vk_bot.handlers import STORAGE_KEY, bot, context_manager
from vk_bot.util import answer, check_closest, get_user_id_from_message_or_event


async def get_user(user_id):
    return (await bot.api.users.get(user_ids=[user_id]))[0]


def get_yes_no_keyboard():
    return (
        Keyboard(one_time=True, inline=False)
        .add(Text("✅ Всё верно"), KeyboardButtonColor.SECONDARY)
        .row()
        .add(Text("❌ Исправить"), KeyboardButtonColor.SECONDARY)
    )


@context_manager.on_state(ActiveState.registration)
async def request_name(
    message_or_event: Message | MessageEvent, session, storage
) -> FinalState:
    user = await get_user(get_user_id_from_message_or_event(message_or_event))
    students = (
        session.query(Student)
        .filter(Student.name.like(f"{user.last_name} {user.first_name}%"))
        .all()
    )
    if len(students) == 1:
        student = students[0]

        storage[STORAGE_KEY.FULL_NAME] = student.name
        storage[STORAGE_KEY.STUDENT_ID] = student.student_id

        await answer(
            message_or_event,
            message=(
                f"❔ Кажется, я нашёл Вас в базе. Давайте проверим данные:\n\n"
                f"👤 Вас зовут:\n{student.name}\n\n"
                f"🆔 Номер студенческого билета:\n{student.student_id}\n\n"
                f"Всё верно?"
            ),
            keyboard=get_yes_no_keyboard().get_json(),
        )

        return FinalState.waiting_for_approve_personal_info

    await answer(
        message_or_event,
        message="📝 Давайте познакомимся! Укажите Ваши фамилию, имя, отчество (при наличии).",
    )
    return FinalState.waiting_for_name


@context_manager.on_state(FinalState.waiting_for_name)
async def process_name_and_request_student_id(message: Message, storage: StorageType):
    name_arr = [n.capitalize() for n in message.text.lower().strip().split()]
    if not 2 <= len(name_arr) <= 3:
        await message.answer(
            "😔 Я не понял Вас :(\nПожалуйста, введите Ваши фамилию, имя, отчество в формате:\nФамилия Имя Отчество (при наличии)."
        )
        return FinalState.waiting_for_name

    full_name = " ".join(name_arr)
    storage[STORAGE_KEY.FULL_NAME] = full_name

    first_name = name_arr[1]
    storage[STORAGE_KEY.FIRST_NAME] = first_name

    await message.answer(
        f"{first_name}, приятно познакомиться! Укажите номер Вашего студенческого билета."
    )
    return FinalState.waiting_for_student_id


@context_manager.on_state(FinalState.waiting_for_student_id)
async def process_student_id_and_request_approve(
    message: Message, storage: StorageType
):
    student_id = message.text
    if not student_id.isdigit():
        await message.answer(
            "😔 Я не понял Вас :(\nНомер студенческого билета должен состоять только из цифр."
        )
        return FinalState.waiting_for_student_id
    storage[STORAGE_KEY.STUDENT_ID] = student_id

    await message.answer(
        f"☑️ Отлично. Давайте проверим данные:\n\n"
        f"👤 Вас зовут:\n{storage[STORAGE_KEY.FULL_NAME]}\n\n"
        f"🆔 Номер студенческого билета:\n{storage[STORAGE_KEY.STUDENT_ID]}\n\n"
        f"Всё верно?",
        keyboard=get_yes_no_keyboard().get_json(),
    )
    return FinalState.waiting_for_approve_personal_info


@context_manager.on_state(FinalState.waiting_for_approve_personal_info)
async def process_approve_personal_info(
    message: Message, session: Session, user: User, storage: StorageType
):
    text = message.text.lower()
    if check_closest(text, ("всё верно", "норм", "да", "верно")):
        student = (
            session.query(Student)
            .filter(Student.student_id == storage[STORAGE_KEY.STUDENT_ID])
            .filter(Student.name == storage[STORAGE_KEY.FULL_NAME])
            .one_or_none()
        )
        if not student:
            await message.answer(
                "😔 К сожалению, я не нашел Вас в базе. Пожалуйста, "
                "проверьте корректность введенных данных и повторите попытку.\n\n"
                f"⚙️ Если это не помогло, обратитесь в поддержку:\n{SUPPORT_CONTACTS}"
            )
            return FinalState.default

        user.student_id = student.id

        await message.answer("🗳️ Отлично! Переходим к голосованию.")
        return ActiveState.voting
    elif check_closest(text, ("исправить", "ошибка", "неверно", "нет")):
        await message.answer("📝 Укажите Ваши фамилию, имя, отчество (при наличии).")
        return FinalState.waiting_for_name

    await message.answer(
        '😔 Не понял Вас :(\nЕсли ввёденные данные корректны, напишите "верно", иначе "исправить".'
    )
    return FinalState.waiting_for_approve_personal_info
