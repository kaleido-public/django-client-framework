from django.core.management.base import BaseCommand
from guardian.utils import clean_orphan_obj_perms as clean_orphan_obj_perms

class Command(BaseCommand):
    help: str
    def handle(self, **options) -> None: ...
