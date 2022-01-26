from typing import Callable, Dict, TypeVar

from django.contrib.auth.models import Group

T = TypeVar("T", bound="Callable")


def register_default_group(
    group_name: str,
) -> Callable[[Callable[[Group], None]], None]:
    def make_decorator(config_group: Callable[[Group], None]) -> None:
        DefaultGroups.group_names[group_name] = config_group

    return make_decorator


def do_nothing(group: Group) -> None:
    pass


class DefaultGroups:
    group_names: Dict[str, Callable[[Group], None]] = {
        "anyone": do_nothing,
    }

    def __getattr__(self, name: str) -> Group:
        if name in self.group_names:
            return Group.objects.get_or_create(name=name)[0]
        else:
            raise AttributeError(f"{name} is not a default group")

    def setup(self) -> None:
        for name, config_func in self.group_names.items():
            group = Group.objects.get_or_create(name=name)[0]
            config_func(group)


default_groups = DefaultGroups()
