import os
import traceback
from datetime import datetime
from functools import wraps

from loguru import logger
from vkbottle import Keyboard, Text
from vkbottle.bot import Message
from vkbottle.dispatch.rules.base import CommandRule, FuncRule, PayloadRule

from models import (
    Candidate,
    Session,
    TGUser,
    User,
    VKUser,
    VoteAgainstAll,
    VoteForCandidate,
    VotingInfo,
)
from models.voter import Voter
from vk_bot.config import USER_CONTEXT_FILE, VK_ADMIN_IDS

from . import bot

SUCCESS_MESSAGE_TEXT = "Действие выполнено успешно."


def _is_admin(message):
    return message.from_id in VK_ADMIN_IDS


def send_exception(func):
    @wraps(func)
    async def wrapper(message: Message):
        try:
            return await func(message)
        except Exception as error:
            logger.error(
                f"An unexpected error has occurred in admin handler: {str(error)}. "
                f"Traceback:\n{traceback.format_exc()}"
            )
            return await message.reply(
                f"При обработке запроса возникла ошибка:\n\n{str(error)}"
            )

    return wrapper


@bot.on.private_message(FuncRule(_is_admin), CommandRule("admin"))
@send_exception
async def admin_commands_menu(message: Message):
    keyboard = (
        Keyboard(inline=True)
        .add(Text("Удалить голоса", {"action": "delete_votes"}))
        .row()
        .add(Text("Удалить пользователей", {"action": "delete_users"}))
        .row()
        .add(Text("Удалить кандидатов", {"action": "delete_candidates"}))
        .row()
        .add(Text("Удалить контекст", {"action": "delete_context"}))
        .row()
        .add(Text("Сгенерировать тестовые данные", {"action": "generate_test_data"}))
    )
    await message.answer("Команды администратора", keyboard=keyboard.get_json())


@bot.on.private_message(FuncRule(_is_admin), PayloadRule({"action": "delete_votes"}))
@send_exception
async def delete_votes(message: Message):
    with Session() as session:
        session.query(VoteAgainstAll).delete()
        session.query(VoteForCandidate).delete()
        session.query(Voter).delete()
        session.commit()

    logger.info(f"Removed votes by vk user {message.from_id}")
    await message.reply(SUCCESS_MESSAGE_TEXT)


@bot.on.private_message(FuncRule(_is_admin), PayloadRule({"action": "delete_users"}))
@send_exception
async def delete_users(message: Message):
    with Session() as session:
        session.query(VKUser).delete()
        session.query(TGUser).delete()
        session.query(User).delete()
        session.commit()

    logger.info(f"Removed users by vk user {message.from_id}")
    await message.reply(SUCCESS_MESSAGE_TEXT)


@bot.on.private_message(
    FuncRule(_is_admin), PayloadRule({"action": "delete_candidates"})
)
@send_exception
async def delete_candidates(message: Message):
    with Session() as session:
        session.query(Candidate).delete()
        session.query(VotingInfo).delete()
        session.commit()

    logger.info(f"Removed candidates by vk user {message.from_id}")
    await message.reply(SUCCESS_MESSAGE_TEXT)


@bot.on.private_message(FuncRule(_is_admin), PayloadRule({"action": "delete_context"}))
@send_exception
async def delete_context(message: Message):
    os.remove(USER_CONTEXT_FILE)
    logger.info(f"Removed context file by vk user {message.from_id}")
    await message.reply(SUCCESS_MESSAGE_TEXT)


candidates_info: dict[int, list] = {
    1: [
        {
            "name": "Беппиев Георгий Игоревич",
            "link": "agentvmk",
            "about": "Как студент первого курса я ещё мало знаю о проблемах факультета, но если они есть, то почему бы не решить их от имени юридического лица?",
        },
        {
            "name": "Дроздова Елизавета Александровна",
            "link": "morinomore",
            "about": "Поклоняюсь идее того, что все должно непрерывно становится лучше, и если можно улучшить что-то, пусть даже мелочь (особенно какую-то мелочь), этим обязательно стоит заняться. С радостью организую что угодно, что меня затянет и вдохновит, и вряд ли меня что-то остановит.",
        },
        {
            "name": "Ренкас Владислав Вячеславович",
            "link": "enofin7",
            "about": "Меня зовут Влад, я совсем недавно поступил на факультет, но при этом уже являюсь довольно активным участником профкома. Я очень общительный человек, легко нахожу общий язык с людьми!",
        },
        {
            "name": "Стрелкина Ирина Викторовна",
            "link": "istrelkina",
            "about": "Я ответственная, хочу сделать факультет лучше и у меня слишком много свободного времени, поэтому я здесь)",
        },
    ],
    2: [
        {
            "name": "Якунин Владимир Петрович",
            "link": "f_to_billy",
            "about": "Я, Якунин Владимир Петрович — студент 2 курса. Считаю себя человеком открытым и всегда готов помочь и ответить на любой вопрос. Люблю и умею ботать, но выборы в студсовет видимо люблю больше бота диффуров). Люблю js и делать margin left 10px.",
        },
        {
            "name": "Хохлов Антон Михайлович",
            "link": "bariron",
            "about": "Являюсь действующим членом студенческого совета. Участвовал в организации многих мероприятий в университете. Член ЦСС по киберспорту.",
        },
        {
            "name": "Волохов Вячеслав Евгеньевич",
            "link": "slavgrd",
            "about": 'На 1 курсе уже был в студсовете, решал проблему с финансированием сборной ВМК по футболу (или мини-футболу) по просьбе самих футболистов. Прислушиваюсь к людям. Бывший редактор паблика "мемгу" (если кто его знает)',
        },
    ],
    3: [
        {
            "name": "Наклескин Никита Владимирович",
            "link": "nnakleskin",
            "about": "Студент кафедры математической физики, член 12 созыва студенческого совета. Активно участвовал в студенческой жизни через участие в студсовете.",
        },
        {
            "name": "Ким Роман Германович",
            "link": "kamerooon",
            "about": "Я сделаю так чтобы жизнь на все стала проще",
        },
        {
            "name": "Саврасов Геннадий Александрович",
            "link": "genbbb",
            "about": "Студент 3 курса и заядлый курильщик",
        },
        {
            "name": "Назарян Марат Гарникович",
            "link": "mnaz2002",
            "about": "Я Марат, студент кафедры СП. Уже два года являюсь председателем Студсовета. Всё пытаюсь развалить его, пока не получилось. Хочу сделать жизнь на факультете комфортней, ярче и слаще. Стараюсь решать проблемы, которые есть на ВМК на бытовом уровне, на уровне образования, стипендний и многого другого. Планирую и дальше предлагать новые идеи и проекты для улучшения нашего факультета.",
        },
        {
            "name": "Ильичев Юрий Алексеевич",
            "link": "gilerby",
            "about": "Меня зовут Юра, приятно познакомиться :) Я учусь на 3 курсе, а в свободное время работаю в Яндексе, благодаря чему имею опыт и знания в сфере разработки B2C-сервисов. Этот опыт я хочу использовать во благо нашего факультета. Мне нравится работать в команде и помогать другим студентам, поэтому я считаю, что студенческий совет - отличная возможность для развития моих навыков и взаимодействия с людьми, а также возможность прислушиваться и учитывать Ваши предложения по оптимизации учебного процесса и развитию нашей Альма-матер.",
        },
    ],
    4: [],
    5: [],
    6: [
        {
            "name": "Волков Андрей Андреевич",
            "link": "id42499509",
            "about": "Привет! Я Волков Андрей, активист с семилетним стажем, знаю факультет юридически и фактически лучше, чем порой учебная часть",
        },
        {
            "name": "Долматов Александр Андреевич",
            "link": "i_zarok_i",
            "about": "Всем привет! Думаю, весь 6-й курс уже давно знаком со мной.\nC осени прошлого года я ваш тот самый староста курса.\nУчился на ВМК в бакалавриате с 2018 по 2022 год. Сейчас студент 2-го курса магистратуры. В баке на 3-м курсе стал старостой группы, на 4-м - старостой потока, с 5-го - староста курса.\nУже четвёртый год нахожусь в тесном, доверительном контакте как со студентами, так и с преподавателями и администрацией.\nУспешно упрощаю жизнь курсу самыми разными способами.\nИду в Студенческий совет с целью решить уже давно наболевшие проблемы, которые тянут факультет на дно.",
        },
    ],
}


@bot.on.private_message(
    FuncRule(_is_admin), PayloadRule({"action": "generate_test_data"})
)
@send_exception
async def generate_test_data(message: Message):
    with Session() as session:
        for course, candidates in candidates_info.items():
            voting_info = VotingInfo(
                faculty="CMC",
                course=course,
                description=f"Анкеты кандидатов: vk.com/@cmcsovet-vybory-2023-{course}-kurs",
                end_time=(d := datetime.utcnow()).replace(year=d.year + 1),
            )
            session.add(voting_info)
            session.flush()

            for candidate in candidates:
                session.add(
                    Candidate(
                        name=candidate["name"],
                        voting_id=voting_info.id,
                        link=candidate["link"],
                        about=candidate["about"],
                        course=course,
                    )
                )

        session.commit()

    logger.info(f"Generate test data by vk user {message.from_id}")
    await message.reply(SUCCESS_MESSAGE_TEXT)
