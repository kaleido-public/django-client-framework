from typing import Any, Callable, Dict, TypeVar

from ..models.abstract.user import DCFAbstractUser, get_dcf_user_model

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

    usernames: Dict[str, Callable[[Any], None]] = {
        "root": do_nothing,
        "anonymous": do_nothing,
    }
    root: DCFAbstractUser
    anonymous: DCFAbstractUser

    def __getattr__(self, name: str) -> DCFAbstractUser:

        if name in self.usernames:
            User = get_dcf_user_model()
            return User.objects.get_or_create(username=name)[0]
        else:
            raise AttributeError(f"{name} is not a default user")

    def setup(self) -> None:
        User = get_dcf_user_model()
        for name, config_func in self.usernames.items():
            user = User.objects.get_or_create(username=name)[0]
            config_func(user)


default_users = DefaultUsers()
