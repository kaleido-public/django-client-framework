from typing import Any

from . import checks as checks

default_app_config: str
VERSION: Any

def get_version(): ...
def monkey_patch_user(): ...
def monkey_patch_group(): ...
