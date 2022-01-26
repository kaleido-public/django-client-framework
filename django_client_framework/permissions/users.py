from typing import Any, Callable, Dict, TypeVar

from ..models import get_user_model
from ..models.abstract.user import DCFAbstractUser

T = TypeVar("T", bound="DCFAbstractUser")


def register_default_user(
    username: str,
) -> Callable[[Callable[[T], None]], None]:
    def make_decorator(config_user: Callable[[T], None]) -> None:
        DefaultUsers.usernames[username] = config_user

    return make_decorator


def do_nothing(user: DCFAbstractUser) -> None:
    pass


class DefaultUsers:

    usernames: Dict[str, Callable[[Any], None]] = {}
    anonymous: DCFAbstractUser

    def __getattr__(self, name: str) -> DCFAbstractUser:
        if name in self.usernames:
            return get_user_model().objects.get_or_create(username=name)[0]
        else:
            raise AttributeError(f"{name} is not a default user")

    def setup(self) -> None:
        DefaultUsers.usernames.setdefault("anonymous", do_nothing)
        for name, config_func in self.usernames.items():
            user = get_user_model().objects.get_or_create(username=name)[0]
            config_func(user)


default_users = DefaultUsers()
