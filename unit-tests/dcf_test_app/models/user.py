from __future__ import annotations

from django_client_framework.models import DCFAbstractUser, DCFModel


class User(DCFModel, DCFAbstractUser):
    pass
