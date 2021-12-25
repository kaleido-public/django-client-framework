from typing import Any

from django import template
from guardian.core import ObjectPermissionChecker as ObjectPermissionChecker
from guardian.exceptions import NotUserNorGroup as NotUserNorGroup

register: Any

class ObjectPermissionsNode(template.Node):
    for_whom: Any
    obj: Any
    context_var: Any
    checker: Any
    def __init__(
        self, for_whom, obj, context_var, checker: Any | None = ...
    ) -> None: ...
    user: Any
    group: Any
    def render(self, context): ...

def get_obj_perms(parser, token): ...
