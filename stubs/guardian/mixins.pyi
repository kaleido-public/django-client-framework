from guardian.shortcuts import get_objects_for_user as get_objects_for_user
from guardian.utils import get_40x_or_None as get_40x_or_None, get_anonymous_user as get_anonymous_user, get_user_obj_perms_model as get_user_obj_perms_model
from typing import Any

UserObjectPermission: Any

class LoginRequiredMixin:
    redirect_field_name: Any
    login_url: Any
    def dispatch(self, request, *args, **kwargs): ...

class PermissionRequiredMixin:
    login_url: Any
    permission_required: Any
    redirect_field_name: Any
    return_403: bool
    return_404: bool
    raise_exception: bool
    accept_global_perms: bool
    any_perm: bool
    def get_required_permissions(self, request: Any | None = ...): ...
    def get_permission_object(self): ...
    def check_permissions(self, request): ...
    def on_permission_check_fail(self, request, response, obj: Any | None = ...) -> None: ...
    request: Any
    args: Any
    kwargs: Any
    def dispatch(self, request, *args, **kwargs): ...

class GuardianUserMixin:
    @staticmethod
    def get_anonymous(): ...
    def add_obj_perm(self, perm, obj): ...
    def del_obj_perm(self, perm, obj): ...

class PermissionListMixin:
    permission_required: Any
    get_objects_for_user_extra_kwargs: Any
    def get_required_permissions(self, request: Any | None = ...): ...
    def get_get_objects_for_user_kwargs(self, queryset): ...
    def get_queryset(self, *args, **kwargs): ...
