import datetime
import json
from typing import Optional
from uuid import uuid4

import vkbottle.exception_factory
from loguru import logger
from sqlalchemy import and_
from sqlalchemy.orm import Session
from vkbottle import Callback, Keyboard, KeyboardButtonColor
from vkbottle.bot import Message, MessageEvent

from models import (
    Candidate,
    Student,
    User,
    VoteAgainstAll,
    VoteForCandidate,
    VotingInfo,
)
from models.voter import Voter
from vk_bot.config import MAX_VOTES_NUMBER, SUPPORT_CONTACTS
from vk_bot.context_manager import ActiveState, FinalState, StateType, StorageType
from vk_bot.handlers import (
    PAYLOAD_ACTION,
    PAYLOAD_KEY,
    STORAGE_KEY,
    bot,
    context_manager,
)
from vk_bot.util import answer


def schedule_deletion(storage, peer_id, message_id):
    try:
        new_message = [peer_id, message_id]
        msg_to_delete = storage.get(STORAGE_KEY.VOTING_MSG_IDS_TO_DELETE, [])
        if new_message not in msg_to_delete:
            msg_to_delete.append(new_message)
        storage[STORAGE_KEY.VOTING_MSG_IDS_TO_DELETE] = msg_to_delete
    except Exception as e:
        logger.error(e)


async def delete_messages(storage):
    for peer_id, message_id in storage.get(STORAGE_KEY.VOTING_MSG_IDS_TO_DELETE, []):
        try:
            await bot.api.messages.delete(
                peer_id=peer_id,
                conversation_message_ids=message_id,
                delete_for_all=True,
            )
        except vkbottle.exception_factory.VKAPIError as e:
            logger.error(f"{str(e)} on message {str(message_id)}")

    storage[STORAGE_KEY.VOTING_MSG_IDS_TO_DELETE] = []


def get_keyboard_with_candidates(
    candidates: list[Candidate], selected_candidate_ids: list[int]
):
    keyboard = Keyboard(inline=True, one_time=False)
    for candidate in candidates:
        color = (
            KeyboardButtonColor.PRIMARY
            if candidate.id in selected_candidate_ids
            else KeyboardButtonColor.SECONDARY
        )
        payload = {
            PAYLOAD_KEY.ACTION: PAYLOAD_ACTION.VOTE_FOR,
            PAYLOAD_KEY.CANDIDATE_ID: candidate.id,
        }
        keyboard.row().add(Callback(candidate.name, json.dumps(payload)), color)

    if not selected_candidate_ids:
        payload = {PAYLOAD_KEY.ACTION: PAYLOAD_ACTION.VOTE_AGAINST_ALL}
        keyboard.row().add(
            Callback("❌ Против всех", json.dumps(payload)),
            KeyboardButtonColor.NEGATIVE,
        )

    if selected_candidate_ids:
        payload = {PAYLOAD_KEY.ACTION: PAYLOAD_ACTION.FINISH_VOTING}
        keyboard.row().add(
            Callback("✅ Закончить голосование", json.dumps(payload)),
            KeyboardButtonColor.POSITIVE,
        )

    return keyboard


def get_candidates(session: Session, user: User) -> list[Candidate]:
    candidates = (
        session.query(Candidate)
        .join(Student, Student.id == user.student_id)
        .join(
            VotingInfo,
            and_(
                VotingInfo.faculty == Student.faculty,
                VotingInfo.course == Student.course,
            ),
        )
        .filter(Candidate.voting_id == VotingInfo.id)
        .filter(Candidate.course == Student.course)
        .order_by(Candidate.id)
        .all()
    )

    logger.info(f"candidates len {len(candidates)}, {candidates}")

    return candidates


def already_voted(session: Session, user: User) -> bool:
    if (
        session.query(VoteAgainstAll)
        .filter(VoteAgainstAll.student_id == user.student_id)
        .all()
    ):
        return True

    if (
        session.query(VoteForCandidate)
        .filter(VoteForCandidate.student_id == user.student_id)
        .all()
    ):
        return True

    if session.query(Voter).filter(Voter.student_id == user.student_id).one_or_none():
        return True

    return False


def get_voting_info(session: Session, user: User) -> Optional[VotingInfo]:
    return (
        session.query(VotingInfo)
        .join(Student, Student.id == user.student_id)
        .filter(Student.faculty == VotingInfo.faculty)
        .filter(Student.course == VotingInfo.course)
        .one_or_none()
    )


async def reaction_on_already_voted(message_or_event, session, user, voting_info):
    voter_uid = (
        session.query(Voter).filter(Voter.student_id == user.student_id).one().voter_uid
    )

    vote_against_all = (
        session.query(VoteAgainstAll)
        .filter(VoteAgainstAll.student_id == user.student_id)
        .one_or_none()
    )
    if vote_against_all:
        info_about_votes = f"за отказ от представительства {voting_info.course} курса в Студенческом совете ВМК."
    else:
        vote_for_candidate = (
            session.query(VoteForCandidate)
            .join(VoteForCandidate.candidate)
            .filter(VoteForCandidate.student_id == user.student_id)
            .all()
        )
        info_about_votes = "за следующих кандидатов:\n\n ◽️ " + "\n ◽️ ".join(
            str(str(vote.candidate.name)) for vote in vote_for_candidate
        )

    await answer(
        message_or_event,
        message=(
            "⚠️ Ваш голос уже есть в базе. \n\n"
            f"🔢 Ваш уникальный номер избирателя:\n{voter_uid}.\n\n"
            f"Вы проголосовали {info_about_votes}\n\n"
            f"⚙️ Если Вы считаете, что произошла ошибка, пожалуйста, обратитесь в поддержку:\n{SUPPORT_CONTACTS}"
        ),
    )
    return FinalState.default


@context_manager.on_state(ActiveState.voting)
async def welcome_to_voting(
    user: User,
    storage: StorageType,
    session: Session,
    message_or_event: Message | MessageEvent,
) -> StateType:
    if not user.student_id:
        return ActiveState.registration

    voting_info = get_voting_info(session, user)
    if not voting_info:
        await answer(
            message_or_event,
            message="🕚 Сейчас нет запущенных голосований. Возвращайтесь позже!",
        )
        return FinalState.default

    if datetime.datetime.utcnow() >= voting_info.end_time:
        await answer(
            message_or_event,
            message="🕚 Голосование уже завершилось. Возвращайтесь позже!",
        )
        return FinalState.default

    if already_voted(session, user):
        return await reaction_on_already_voted(
            message_or_event, session, user, voting_info
        )

    candidates = get_candidates(session, user)
    if len(candidates) == 0:
        await answer(
            message_or_event,
            message=(
                f"🙁 К сожалению, на {voting_info.course} курсе никто не выдвинул свою кандидатуру "
                "в члены Студенческого совета ВМК. Ваш курс будет считаться "
                "отказавшимся от представительства в совете."
            ),
        )
        return FinalState.default

    votes_for = storage.get(STORAGE_KEY.VOTES_FOR, [])
    votes_for = list(set(votes_for) & set(c.id for c in candidates))
    storage[STORAGE_KEY.VOTES_FOR] = votes_for[:MAX_VOTES_NUMBER]
    if len(votes_for) >= MAX_VOTES_NUMBER or storage.get(STORAGE_KEY.VOTE_AGAINST_ALL):
        return ActiveState.confirm_votes

    keyboard = get_keyboard_with_candidates(candidates, votes_for)
    text = f"☑️ На {voting_info.course} курсе зарегистрированы следующие кандидаты: \n\n"
    for candidate in candidates:
        text += f" ◽️ [{candidate.link}|{candidate.name}]\n ℹ️ {candidate.about}\n\n"
    if voting_info.description:
        text += f"{voting_info.description}\n\n"
    if first_name := storage.get(STORAGE_KEY.FIRST_NAME):
        text += f"{first_name}, "
    text += (
        f"Вы можете выбрать не более {MAX_VOTES_NUMBER} кандидатов.\n"
        "Также Вы можете проголосовать против всех "
        f"(в этом случае Вы голосуете за отказ от представительства {voting_info.course} курса в Студенческом совете).\n\n"
        "ℹ️ Нажмите на кнопки внизу сообщения с именами кандидатов, за которых хотите проголосовать. "
        "Выбранные кандидаты будут подсвечены на клавиатуре. Чтобы отменить выбор, "
        "ещё раз нажмите на кнопку с кандидатом.\n"
        'После того, как выберете кандидатов, нажмите кнопку "Закончить голосование".'
    )

    if isinstance(message_or_event, Message):
        await delete_messages(storage)
    conversation_message_id = await answer(
        message_or_event,
        message=text,
        keyboard=keyboard.get_json(),
    )
    schedule_deletion(storage, message_or_event.peer_id, conversation_message_id)

    return FinalState.process_vote


@context_manager.on_state(FinalState.process_vote)
async def process_vote(storage: StorageType, event: MessageEvent):
    if not event.payload:
        return ActiveState.voting

    match event.payload.get(PAYLOAD_KEY.ACTION):
        case PAYLOAD_ACTION.FINISH_VOTING:
            return ActiveState.confirm_votes

        case PAYLOAD_ACTION.VOTE_AGAINST_ALL:
            storage[STORAGE_KEY.VOTE_AGAINST_ALL] = True
            storage[STORAGE_KEY.VOTES_FOR] = []
            return ActiveState.confirm_votes

        case PAYLOAD_ACTION.VOTE_FOR:
            if not (
                selected_candidate_id := event.payload.get(PAYLOAD_KEY.CANDIDATE_ID)
            ):
                return ActiveState.confirm_votes

            votes_for = storage.get(STORAGE_KEY.VOTES_FOR, [])
            if selected_candidate_id in votes_for:
                votes_for.remove(selected_candidate_id)
            else:
                if len(votes_for) < MAX_VOTES_NUMBER:
                    votes_for.append(selected_candidate_id)

            storage[STORAGE_KEY.VOTES_FOR] = votes_for

            if len(votes_for) >= MAX_VOTES_NUMBER:
                return ActiveState.confirm_votes

            return ActiveState.voting

    return ActiveState.voting


@context_manager.on_state(ActiveState.confirm_votes)
async def confirm_votes(
    storage: StorageType,
    session,
    user,
    message_or_event: Message | MessageEvent,
):
    if not user.student_id:
        return ActiveState.registration

    voting_info = get_voting_info(session, user)
    if already_voted(session, user):
        return await reaction_on_already_voted(
            message_or_event, session, user, voting_info
        )

    confirm_payload = {
        PAYLOAD_KEY.ACTION: PAYLOAD_ACTION.CONFIRM_VOTING,
        PAYLOAD_KEY.VALUE: True,
    }
    not_confirm_payload = {
        PAYLOAD_KEY.ACTION: PAYLOAD_ACTION.CONFIRM_VOTING,
        PAYLOAD_KEY.VALUE: False,
    }

    keyboard = (
        Keyboard(inline=True)
        .add(Callback("✅ Да", json.dumps(confirm_payload)))
        .add(Callback("❌ Нет", json.dumps(not_confirm_payload)))
    )

    state: StateType
    if storage.get(STORAGE_KEY.VOTE_AGAINST_ALL):
        msg = "❔ Вы уверены, что хотите проголосовать против всех?"
        keyboard = keyboard.get_json()
        state = FinalState.waiting_for_confirm_votes
    elif votes := storage.get(STORAGE_KEY.VOTES_FOR):
        msg = (
            "❔ Вы хотите проголосовать за:\n\n ◽️ "
            + "\n ◽️ ".join(
                str(candidate.name)
                for candidate in get_candidates(session, user)
                if candidate.id in votes
            )
            + "\n\nВерно?"
        )
        keyboard = keyboard.get_json()
        state = FinalState.waiting_for_confirm_votes
    else:
        msg = "❗️ Вы еще ни за кого не проголосовали."
        keyboard = None
        state = ActiveState.voting

    if isinstance(message_or_event, Message):
        await delete_messages(storage)
    conversation_message_id = await answer(
        message_or_event, message=msg, keyboard=keyboard
    )
    schedule_deletion(storage, message_or_event.peer_id, conversation_message_id)
    return state


@context_manager.on_state(FinalState.waiting_for_confirm_votes)
async def waiting_for_confirm_votes(
    event: MessageEvent, storage: StorageType, session: Session, user: User
):
    if (
        event.payload is None
        or event.payload.get(PAYLOAD_KEY.ACTION) != PAYLOAD_ACTION.CONFIRM_VOTING
    ):
        return ActiveState.voting

    voting_info = get_voting_info(session, user)
    if already_voted(session, user):
        return await reaction_on_already_voted(event, session, user, voting_info)

    if not (
        storage.get(STORAGE_KEY.VOTE_AGAINST_ALL) or storage.get(STORAGE_KEY.VOTES_FOR)
    ):
        await answer(event, message="❗️ Вы еще ни за кого не проголосовали.")
        return ActiveState.voting

    if voting_info is None:
        await answer(
            event, message="🕚 Сейчас нет запущенных голосований. Возвращайтесь позже!"
        )
        return FinalState.default

    db_votes: list[VoteForCandidate | VoteAgainstAll]
    if event.payload.get(PAYLOAD_KEY.VALUE) is True:
        text = "🗳️ Спасибо за участие, Ваш голос учтен! Вы проголосовали "
        if storage.get(STORAGE_KEY.VOTE_AGAINST_ALL):
            db_votes = [
                VoteAgainstAll(
                    user_id=user.id,
                    student_id=user.student_id,
                    voting_id=voting_info.id,
                )
            ]
            text += f"за отказ от представительства {voting_info.course} курса в Студенческом совете ВМК."
        else:
            votes_for = storage.get(STORAGE_KEY.VOTES_FOR, [])
            db_votes = [
                VoteForCandidate(
                    user_id=user.id,
                    student_id=user.student_id,
                    candidate_id=candidate.id,
                    voting_id=candidate.voting_id,
                )
                for candidate in get_candidates(session, user)
                if candidate.id in votes_for
            ]
            text += "за следующих кандидатов:\n\n ◽️ " + "\n ◽️ ".join(
                str(candidate.name)
                for candidate in get_candidates(session, user)
                if candidate.id in votes_for
            )

        voter_uid = uuid4().hex[:10]
        text += (
            f"\n\n🔢 Ваш уникальный номер избирателя:\n{voter_uid}.\n\n"
            "По нему в конце голосования Вы сможете убедиться, "
            "что Ваш голос учёлся правильно."
        )

        session.add_all(db_votes)
        session.add(
            Voter(
                student_id=user.student_id,
                voting_id=voting_info.id,
                voter_uid=voter_uid,
                user_id=user.id,
            )
        )
        session.flush()

        await answer(event, message=text)
    else:
        storage[STORAGE_KEY.VOTE_AGAINST_ALL] = False
        if len(storage.get(STORAGE_KEY.VOTES_FOR, [])) >= MAX_VOTES_NUMBER:
            storage[STORAGE_KEY.VOTES_FOR] = storage.get(STORAGE_KEY.VOTES_FOR, [])[
                : MAX_VOTES_NUMBER - 1
            ]

        return ActiveState.voting
