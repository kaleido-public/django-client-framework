from . import monkey_patch_group as monkey_patch_group, monkey_patch_user as monkey_patch_user
from django.apps import AppConfig
from guardian.conf import settings as settings

class GuardianConfig(AppConfig):
    name: str
    default_auto_field: str
    def ready(self) -> None: ...
