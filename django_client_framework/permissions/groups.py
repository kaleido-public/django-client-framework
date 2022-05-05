from typing import Callable, Dict, TypeVar

from ..models import UserGroup

T = TypeVar("T", bound="Callable")


def register_default_group(
    group_name: str,
) -> Callable[[Callable[[UserGroup], None]], None]:
    def make_decorator(config_group: Callable[[UserGroup], None]) -> None:
        DefaultGroups.group_names[group_name] = config_group

    return make_decorator


def do_nothing(group: UserGroup) -> None:
    pass


class DefaultGroups:
    group_names: Dict[str, Callable[[UserGroup], None]] = {
        "anyone": do_nothing,
    }
    anyone: UserGroup

    def __getattr__(self, name: str) -> UserGroup:
        if name in self.group_names:
            return UserGroup.objects.get_or_create(name=name)[0]
        else:
            raise AttributeError(f"{name} is not a default group")

    def setup(self) -> None:
        for name, config_func in self.group_names.items():
            group = UserGroup.objects.get_or_create(name=name)[0]
            config_func(group)


default_groups = DefaultGroups()
