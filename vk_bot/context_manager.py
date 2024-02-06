import inspect
import json
from asyncio import Semaphore
from enum import Enum
from functools import partial, wraps
from types import MappingProxyType
from typing import Any, Callable, Coroutine, Optional

from loguru import logger
from sqlalchemy.orm import Session
from vedis import Vedis
from vkbottle.bot import Message, MessageEvent

from models import SessionMaker, User, VKUser
from vk_bot.util import WrongObjectType, get_user_id_from_message_or_event

USER_CONTEXT_FILE = ".user_context"


class FinalState(Enum):
    default = "default"
    command_selection = "command_selection"
    process_vote = "process_vote"

    waiting_for_name = "waiting_for_name"
    waiting_for_student_id = "waiting_for_student_id"
    waiting_for_approve_personal_info = "waiting_for_approve_personal_info"

    waiting_for_confirm_votes = "waiting_for_confirm_votes"


class ActiveState(Enum):
    welcome = "welcome"
    voting = "voting"
    registration = "registration"
    confirm_votes = "confirm_votes"
    help = "help"


StateType = FinalState | ActiveState


class UserContext:
    def __init__(self, state: FinalState, storage: dict):
        self.state = state
        self.storage = storage

    def __repr__(self):
        return f"{self.state} {self.storage}"


def get_context(user_id: int) -> UserContext:
    with Vedis(USER_CONTEXT_FILE) as db:
        try:
            json_state = json.loads(db[user_id].decode())
            return UserContext(FinalState(json_state["state"]), json_state["storage"])
        except (KeyError, json.JSONDecodeError):
            return UserContext(FinalState.default, {})


def set_context(user_id: int, user_context: UserContext) -> bool:
    if not (
        isinstance(user_context.state, FinalState)
        and isinstance(user_context.storage, dict)
    ):
        return False

    with Vedis(USER_CONTEXT_FILE) as db:
        try:
            db[user_id] = json.dumps(
                {
                    "state": user_context.state.value,
                    "storage": user_context.storage,
                }
            )
            return True
        except Exception as error:
            logger.error(error)
            return False


StorageType = dict
MessageHandlerType = Callable[[Message], Coroutine[Any, Any, None]]
EventHandlerType = Callable[[MessageEvent], Coroutine[Any, Any, None]]
HandlerType = Callable[[Any], Coroutine[Any, Any, None]]


def _validate_handler_args(args: MappingProxyType[str, inspect.Parameter]) -> bool:
    extra_args = set(args.keys()) - {
        "message",
        "event",
        "message_or_event",
        "storage",
        "session",
        "user",
    }
    if extra_args:
        logger.error(
            f'The function has extra arguments: {", ".join(extra_args)}')
        return False
    return True


def _get_or_create_user(session: Session, vk_id: int) -> User:
    user = (
        session.query(User)
        .join(User.vk_users)
        .filter(VKUser.vk_id == vk_id)
        .with_for_update()
        .one_or_none()
    )
    if not user:
        user = User(vk_users=[VKUser(vk_id=vk_id)])
        session.add(user)
        session.commit()

    return user


class HandlerNotFoundError(NotImplementedError):
    def __init__(self, handler_type: str, state_name: str) -> None:
        super().__init__(
            f"The {handler_type} handler for the {state_name} state was not found"
        )


class ContextManager:
    def __init__(self):
        self._message_handlers: dict[StateType | None, MessageHandlerType] = {}
        self._event_handlers: dict[StateType | None, EventHandlerType] = {}
        self._semaphores: dict[int, Semaphore] = {}

    def on_state(self, *states: StateType | None):
        def wrapper(handler) -> MessageHandlerType | EventHandlerType:
            handler_args = inspect.signature(handler).parameters.keys()

            @wraps(handler)
            async def helper(message_or_event: Message | MessageEvent) -> None:
                user_id = get_user_id_from_message_or_event(message_or_event)

                context = get_context(user_id)
                storage = context.storage

                parameterized_handler = handler

                if "storage" in handler_args:
                    parameterized_handler = partial(handler, storage=storage)

                if "message" in handler_args and isinstance(message_or_event, Message):
                    parameterized_handler = partial(
                        parameterized_handler, message=message_or_event
                    )

                if "event" in handler_args and isinstance(
                    message_or_event, MessageEvent
                ):
                    parameterized_handler = partial(
                        parameterized_handler, event=message_or_event
                    )

                if "message_or_event" in handler_args:
                    parameterized_handler = partial(
                        parameterized_handler, message_or_event=message_or_event
                    )

                if "user" or "session" in handler_args:
                    with SessionMaker() as session:
                        kwargs: dict[str, Any] = {}
                        if "user" in handler_args:
                            kwargs["user"] = _get_or_create_user(
                                session, user_id)
                        if "session" in handler_args:
                            kwargs["session"] = session

                        try:
                            next_state = await parameterized_handler(**kwargs)
                        except Exception:
                            session.rollback()
                            raise
                        else:
                            session.commit()
                else:
                    next_state = await parameterized_handler()

                if isinstance(next_state, FinalState):
                    set_context(user_id, UserContext(next_state, storage))
                elif isinstance(next_state, ActiveState):
                    set_context(user_id, UserContext(context.state, storage))
                    next_handler = self._get_handler_by_state(
                        message_or_event, next_state
                    )
                    if next_handler:
                        await next_handler(message_or_event)
                    else:
                        raise ValueError(
                            f"There is no handler for the {next_state.value} state"
                        )

            if not _validate_handler_args(inspect.signature(handler).parameters):
                raise TypeError(
                    f"The signature of the {handler.__name__} handler is incorrect"
                )

            for state in states:
                if {"message", "message_or_event"}.intersection(handler_args):
                    self._message_handlers[state] = helper
                if {"event", "message_or_event"}.intersection(handler_args):
                    self._event_handlers[state] = helper
                    logger.info(
                        f"register {helper.__name__} for {handler_args}")

            return helper

        return wrapper

    def get_handler(self, message_or_event) -> Optional[HandlerType]:
        user_id = get_user_id_from_message_or_event(message_or_event)
        context = get_context(user_id)

        handler = self._get_handler_by_state(message_or_event, context.state)
        handler = handler or self._get_handler_by_state(
            message_or_event, FinalState.default
        )
        if not handler:
            return None
        # if not handler:
        #     raise HandlerNotFoundError(str(type(message_or_event)), context.state.value)

        return self._handler_with_semaphore(handler)

    def _handler_with_semaphore(self, handler: HandlerType):
        async def wrapper(message_or_event):
            user_id = get_user_id_from_message_or_event(message_or_event)
            await self._acquire_semaphore(user_id)
            try:
                return await handler(message_or_event)
            finally:
                self._release_semaphore(user_id)

        return wrapper

    def _get_handler_by_state(self, message_or_event, state) -> Optional[HandlerType]:
        if isinstance(message_or_event, Message):
            return self._message_handlers.get(state)
        elif isinstance(message_or_event, MessageEvent):
            return self._event_handlers.get(state)
        else:
            raise WrongObjectType("message_or_event", type(message_or_event))

    async def _acquire_semaphore(self, user_id):
        if self._semaphores.get(user_id) is None:
            self._semaphores[user_id] = Semaphore()
        await self._semaphores[user_id].acquire()

    def _release_semaphore(self, user_id):
        if self._semaphores.get(user_id) is None:
            return
        self._semaphores[user_id].release()
