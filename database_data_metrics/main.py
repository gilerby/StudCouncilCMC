from typing import Any
from wsgiref.simple_server import make_server

from prometheus_client import REGISTRY as PROMETHEUS_REGISTRY
from prometheus_client import CollectorRegistry, make_wsgi_app
from prometheus_client.metrics_core import GaugeMetricFamily
from sqlalchemy import func

from models import (
    Candidate,
    SessionMaker,
    Student,
    TGUser,
    User,
    VKUser,
    VoteAgainstAll,
    VoteForCandidate,
    VotingInfo,
)


class NumberOfUsersCollector(CollectorRegistry):
    def __init__(self):
        self.metric_name = "number_of_users"
        self.metric_help = "Количество пользователей"

    def collect(self):
        metric_family = GaugeMetricFamily(
            self.metric_name, self.metric_help, labels=["category"]
        )

        with SessionMaker() as session:
            associated_with_student_users_number = (
                session.query(User).filter(User.student_id.is_not(None)).count()
            )
            metric_family.add_metric(
                ["associated_with_student"], associated_with_student_users_number
            )

            for category, table in (
                ("all", User),
                ("telegram", TGUser),
                ("vk", VKUser),
            ):
                metric_family.add_metric([category], session.query(table).count())

        yield metric_family


class VotesByCandidatesCollector(CollectorRegistry):
    def __init__(self):
        self.metric_name = "votes_by_candidates"
        self.metric_help = "Голоса за кандидатов"

    def collect(self):
        metric_family = GaugeMetricFamily(
            self.metric_name,
            self.metric_help,
            labels=["course", "votes_category", "candidate_name"],
        )

        with SessionMaker() as session:
            votes_for_candidates: dict[int, Any] = {
                row.candidate_id: row.count
                for row in session.query(
                    VoteForCandidate.candidate_id, func.count().label("count")
                )
                .join(Candidate, Candidate.id == VoteForCandidate.candidate_id)
                .join(VotingInfo, Candidate.voting_id == VotingInfo.id)
                .group_by(VotingInfo.course, VoteForCandidate.candidate_id)
                .all()
            }
            votes_against_all: dict[int, Any] = {
                row.course: row.count
                for row in session.query(Student.course, func.count().label("count"))
                .select_from(VoteAgainstAll)
                .join(Student, Student.id == VoteAgainstAll.student_id)
                .group_by(Student.course)
                .all()
            }
            candidates = (
                session.query(VotingInfo.course, Candidate.id, Candidate.name)
                .join(VotingInfo, Candidate.voting_id == VotingInfo.id)
                .all()
            )

        for candidate in candidates:
            metric_family.add_metric(
                [str(candidate.course), "votes_for_candidate", candidate.name],
                votes_for_candidates.get(candidate.id, 0),
            )

        for course in set(map(lambda c: c.course, candidates)) | set(
            votes_against_all.keys()
        ):
            metric_family.add_metric(
                [str(course), "votes_against_all", ""], votes_against_all.get(course, 0)
            )

        yield metric_family


class NumberOfStudentsWhoVotedCollector(CollectorRegistry):
    def __init__(self):
        self.metric_name = "number_of_students_who_voted"
        self.metric_help = "Количество проголосовавших студентов"

    def collect(self):
        metric_family = GaugeMetricFamily(
            self.metric_name, self.metric_help, labels=["course"]
        )

        with SessionMaker() as session:
            votes_for_candidates: dict[int, Any] = {
                row.course: row.count
                for row in session.query(
                    VotingInfo.course,
                    func.count(VoteForCandidate.student_id.distinct()).label("count"),
                )
                .join(Candidate, Candidate.id == VoteForCandidate.candidate_id)
                .join(VotingInfo, Candidate.voting_id == VotingInfo.id)
                .group_by(VotingInfo.course)
                .all()
            }

            votes_against_all: dict[int, Any] = {
                row.course: row.count
                for row in session.query(Student.course, func.count().label("count"))
                .select_from(VoteAgainstAll)
                .join(Student, Student.id == VoteAgainstAll.student_id)
                .group_by(Student.course)
                .all()
            }

            courses = set(votes_for_candidates.keys()) | set(votes_against_all.keys())
            for course in courses:
                metric_family.add_metric(
                    [str(course)],
                    votes_for_candidates.get(course, 0)
                    + votes_against_all.get(course, 0),
                )

        yield metric_family


def start():
    PROMETHEUS_REGISTRY.register(NumberOfUsersCollector())
    PROMETHEUS_REGISTRY.register(VotesByCandidatesCollector())
    PROMETHEUS_REGISTRY.register(NumberOfStudentsWhoVotedCollector())

    app = make_wsgi_app()
    httpd = make_server("", 8000, app)
    httpd.serve_forever()


if __name__ == "__main__":
    start()
