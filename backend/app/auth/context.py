"""Request-scoped current-username, set by get_current_user, read by persistence."""
from contextvars import ContextVar

_current_username: ContextVar[str | None] = ContextVar("current_username", default=None)


def set_current_username(username: str | None) -> None:
    _current_username.set(username)


def get_current_username() -> str | None:
    return _current_username.get()
