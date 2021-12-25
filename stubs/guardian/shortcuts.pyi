from guardian.core import ObjectPermissionChecker as ObjectPermissionChecker
from guardian.ctypes import get_content_type as get_content_type
from guardian.exceptions import (
    MixedContentTypeError as MixedContentTypeError,
    MultipleIdentityAndObjectError as MultipleIdentityAndObjectError,
    WrongAppError as WrongAppError,
)
from guardian.utils import (
    get_anonymous_user as get_anonymous_user,
    get_group_obj_perms_model as get_group_obj_perms_model,
    get_identity as get_identity,
    get_user_obj_perms_model as get_user_obj_perms_model,
)
from typing import Any

GroupObjectPermission: Any
UserObjectPermission: Any

def assign_perm(perm: Any, user_or_group: Any, obj: Any | None = ...) -> Any: ...
def assign(perm: Any, user_or_group: Any, obj: Any | None = ...) -> Any: ...
def remove_perm(
    perm: Any, user_or_group: Any | None = ..., obj: Any | None = ...
) -> Any: ...
def get_perms(user_or_group: Any, obj: Any) -> Any: ...
def get_user_perms(user: Any, obj: Any) -> Any: ...
def get_group_perms(user_or_group: Any, obj: Any) -> Any: ...
def get_perms_for_model(cls: Any) -> Any: ...
def get_users_with_perms(
    obj: Any,
    attach_perms: bool = ...,
    with_superusers: bool = ...,
    with_group_users: bool = ...,
    only_with_perms_in: Any | None = ...,
) -> Any: ...
def get_groups_with_perms(obj: Any, attach_perms: bool = ...) -> Any: ...
def get_objects_for_user(
    user: Any,
    perms: Any,
    klass: Any | None = ...,
    use_groups: bool = ...,
    any_perm: bool = ...,
    with_superuser: bool = ...,
    accept_global_perms: bool = ...,
) -> Any: ...
def get_objects_for_group(
    group: Any,
    perms: Any,
    klass: Any | None = ...,
    any_perm: bool = ...,
    accept_global_perms: bool = ...,
) -> Any: ...
