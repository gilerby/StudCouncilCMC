from typing import Type

from sqlalchemy import and_

from models import *
from uuid import uuid4
from tg_bot.utils import max_can


def get_candidates(session: Session, user: User) -> list[Type[Candidate]]:
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

    return candidates

#имеет смысл проверять при старте
#имеет смысл проверять всегда?
def get_or_create_user(session: Session, tg_id):
    user = session.query(User) \
        .join(TGUser, TGUser.user_id == User.id) \
        .filter(TGUser.tg_id == tg_id) \
        .one_or_none()
    if not user:
        user = User()
        session.add(user)
        session.commit()

        tg_user = TGUser(tg_id=tg_id, user_id=user.id)
        session.add(tg_user)
        session.commit()
    return user

def already_voted(session: Session, user: User):

    if session.query(VoteAgainstAll).filter(VoteAgainstAll.student_id == user.student_id).all():
        return True

    if session.query(VoteForCandidate).filter(VoteForCandidate.student_id == user.student_id).all():
        return True

    return False

#database query ckecing the name and stud_id
def name_in_studlist(session: Session, storage: dict):
    tmp =  session.query(Student) \
                  .filter(Student.student_id == storage['stud_id']) \
                  .filter(Student.name == storage['name']) \
                  .one_or_none()  
    return tmp


def add_studID(session:Session, storage:dict, user: User) -> None:
    user.student_id = name_in_studlist(session, storage).id
    session.commit()

def get_voting_info(session: Session, user: User):
    return (
        session.query(VotingInfo)
        .join(Student, Student.id == user.student_id)
        .filter(Student.faculty == VotingInfo.faculty)
        .filter(Student.course == VotingInfo.course)
        .one_or_none()
    )


def vote_to_database(session: Session, storage:dict, user:User)->str:

    voter_uid = uuid4().hex[:10]
    voting_id = get_voting_info(session,user).id

    if storage['against_all']:
        
        db_votes = [VoteAgainstAll(user_id=user.id, student_id=user.student_id, voting_id=voting_id)]
        msg = "Спасибо за участие! Ваш голос учтен! \
	            \n\nВы проголосовали за отказ от представительства курса в Студенческом совете." \
               + f"\n\n\n\nВаш уникальный номер избирателя: \n\n<tg-spoiler>{voter_uid}</tg-spoiler> "
        
    elif storage['candidats']: 
        db_votes = [VoteForCandidate(user_id=user.id, student_id=user.student_id, candidate_id=candidate.id, voting_id = voting_id) for
                    candidate in get_candidates(session, user) if
                    candidate.id in storage['candidats']]
        


        msg = "Спасибо за участие! Ваш голос учтен! \
                \n\nВы проголосовали за:"+"\n\n✔️"  + "\n\n✔️".join(map (lambda vote: vote.name, get_id_from_candidat(storage["candidats"], get_candidates(session, user))) )   \
                + f"\n\n\nВаш уникальный номер  избирателя:\n\n<tg-spoiler>{voter_uid}</tg-spoiler> "
    session.add_all(db_votes)
    session.add(Voter(student_id=user.student_id, voting_id=voting_id, voter_uid=voter_uid, user_id=user.id))
    session.commit()
    return msg   

    

def prepare_candidat_info(session: Session, user: User):
    candidates = get_candidates(session, user)
    voting_info = get_voting_info(session, user)
    text = f"☑️ На {voting_info.course} курсе зарегистрированы следующие кандидаты: \n\n"
    for candidate in candidates:
        text += f" ◽️ {candidate.name}\n ℹ️ {candidate.about}\n\n"
    if voting_info.description:
        text += f"{voting_info.description}\n\n"

    text += (
        f"Вы можете выбрать не более {max_can} кандидатов.\n"
        "Также Вы можете проголосовать против всех "
        f"(в этом случае Вы голосуете за отказ от представительства {voting_info.course} курса в Студенческом совете).\n\n"
        "ℹ️ Нажмите на кнопки внизу сообщения с именами кандидатов, за которых хотите проголосовать. "
        "Выбранные кандидаты будут подсвечены на клавиатуре. Чтобы отменить выбор, "
        "ещё раз нажмите на кнопку с кандидатом.\n"
        'После того, как выберете кандидатов, нажмите кнопку "Закончить голосование".'
    )

    return text
def get_id_from_candidat(idx: list[int], candidats: list[User]):
    return list(filter(lambda x: x.id in idx, candidats))




