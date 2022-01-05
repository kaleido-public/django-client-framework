from typing import Callable, Dict

from ..models import get_user_model
from ..models.abstract.user import DCFAbstractUser


def register_default_user(
    username: str,
) -> Callable[[Callable[[DCFAbstractUser], None]], None]:
    def make_decorator(config_user: Callable[[DCFAbstractUser], None]) -> None:
        DefaultUsers.usernames[username] = config_user

    return make_decorator


def do_nothing(user: DCFAbstractUser) -> None:
    pass


class DefaultUsers:

    usernames: Dict[str, Callable[[DCFAbstractUser], None]] = {}

    def __getattr__(self, name: str) -> DCFAbstractUser:
        if name in self.usernames:
            return get_user_model().objects.get_or_create(username=name)[0]
        else:
            raise AttributeError(f"{name} is not a default user")

    def setup(self) -> None:
        for name, config_func in self.usernames.items():
            user = get_user_model().objects.get_or_create(username=name)[0]
            config_func(user)

    @property
    def anonymous(self) -> DCFAbstractUser:
        return get_user_model().get_anonymous()


default_users = DefaultUsers()
