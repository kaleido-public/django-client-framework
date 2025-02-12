from typing import *

from django.apps import AppConfig
from django.db.models import signals


class DefaultApp(AppConfig):
    name = "django_client_framework"

    def ready(self) -> None:
        """
        Although you can access model classes as described above, avoid interacting with
        the database in your ready() implementation. This includes model methods that
        execute queries (save(), delete(), manager methods etc.), and also raw SQL
        queries via django.db.connection. Your ready() method will run during startup of
        every management command. For example, even though the test database
        configuration is separate from the production settings, manage.py test would
        still execute some queries against your production database!
        """

        from django.conf import settings

        from . import models  # noqa

        signals.post_migrate.connect(post_migrate, sender=self)

        if settings.DEBUG:
            from . import api, serializers

            api.check_integrity()
            models.check_integrity()
            serializers.check_integrity()


def post_migrate(*args: Any, **kwargs: Any) -> None:
    from .permissions import default_groups, default_users
    from .permissions.site_permission import _get_permission_for_model

    _get_permission_for_model.cache_clear()
    default_groups.setup()
    default_users.setup()
