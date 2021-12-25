from typing import Any

from guardian.ctypes import get_content_type as get_content_type
from guardian.exceptions import NotUserNorGroup as NotUserNorGroup

logger: Any
abspath: Any

def get_anonymous_user(): ...
def get_identity(identity): ...
def get_40x_or_None(
    request: Any,
    perms: Any,
    obj: Any | None = ...,
    login_url: Any | None = ...,
    redirect_field_name: Any | None = ...,
    return_403: bool = ...,
    return_404: bool = ...,
    accept_global_perms: bool = ...,
    any_perm: bool = ...,
) -> Any: ...
def get_obj_perm_model_by_conf(setting_name): ...
def clean_orphan_obj_perms(): ...
def get_obj_perms_model(obj, base_cls, generic_cls): ...
def get_user_obj_perms_model(obj: Any | None = ...) -> Any: ...
def get_group_obj_perms_model(obj: Any | None = ...) -> Any: ...
def evict_obj_perms_cache(obj): ...
