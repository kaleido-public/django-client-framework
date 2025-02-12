import uuid
from typing import *

from django.db.models.fields.related import OneToOneField


def monkeypatch_djangotypes() -> None:
    # Monkey patch for django-types
    # https://github.com/sbdchd/django-types
    # in settings.py
    from django.db.models import ForeignKey
    from django.db.models.manager import BaseManager
    from django.db.models.query import QuerySet

    # NOTE: there are probably other items you'll need to monkey patch depending on
    # your version.
    for cls in [QuerySet, BaseManager, ForeignKey, OneToOneField]:
        cls.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore [attr-defined]


def monkeypatch_abstract_generic() -> None:
    # Monkey patch for django-types See
    # https://github.com/typeddjango/django-stubs/issues/299 in settings.py
    from typing import Generic

    from django.db.migrations.state import ModelState

    _original = ModelState.render

    def _new(model: Any, apps: Any) -> Any:
        model.bases = tuple(base for base in model.bases if base is not Generic)  # type: ignore
        return _original(model, apps)

    ModelState.render = _new  # type: ignore


def monkeypatch_pk_field(app_name: str) -> None:
    """Forces all generated models for ManyToManyFields to use UUID primary key.
    This is needed until Django natively supports using UUID pk field."""
    from django.db.models import UUIDField
    from django.db.models.options import Options

    original = None  # type: ignore

    class UUIDPKField(UUIDField):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            kwargs.pop("auto_created", None)
            kwargs["default"] = uuid.uuid4
            super().__init__(*args, **kwargs)

    def patch_get_default_pk_class(
        self: Any, *args: Any, **kwargs: Any
    ) -> Type[UUIDPKField]:
        if self.db_table.startswith(f"{app_name}_"):
            return UUIDPKField
        else:
            return original(self, *args, **kwargs)  # type: ignore

    if Options._get_default_pk_class is not patch_get_default_pk_class:  # type:ignore
        original = Options._get_default_pk_class  # type: ignore
        Options._get_default_pk_class = patch_get_default_pk_class  # type:ignore


def install(
    INSTALLED_APPS: List[str],
    REST_FRAMEWORK: Any,
    MIDDLEWARE: List[str],
    AUTHENTICATION_BACKENDS: List[str],
) -> None:
    INSTALLED_APPS += [
        "rest_framework",
        "django_client_framework.apps.DefaultApp",
    ]
    MIDDLEWARE += [
        "django_client_framework.exceptions.handlers.ConvertAPIExceptionToJsonResponse",
    ]
    REST_FRAMEWORK.update(
        {
            "EXCEPTION_HANDLER": "django_client_framework.exceptions.handlers.dcf_exception_handler",
            "NON_FIELD_ERRORS_KEY": "non_field",
        }
    )
    AUTHENTICATION_BACKENDS += []

    monkeypatch_abstract_generic()
    monkeypatch_djangotypes()
    monkeypatch_pk_field("django_client_framework")
