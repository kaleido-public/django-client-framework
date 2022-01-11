from typing import Any, List

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


def install(
    INSTALLED_APPS: List[str],
    REST_FRAMEWORK: Any,
    MIDDLEWARE: List[str],
    AUTHENTICATION_BACKENDS: List[str],
) -> None:
    INSTALLED_APPS += [
        "rest_framework",
        "guardian",
        "django_client_framework.apps.DefaultApp",
    ]
    MIDDLEWARE += [
        "django_client_framework.exceptions.handlers.ConvertAPIExceptionToJsonResponse",
        "django_currentuser.middleware.ThreadLocalUserMiddleware",
    ]
    REST_FRAMEWORK.update(
        {
            "EXCEPTION_HANDLER": "django_client_framework.exceptions.handlers.dcf_exception_handler",
            "NON_FIELD_ERRORS_KEY": "general_errors",
        }
    )
    AUTHENTICATION_BACKENDS += [
        "guardian.backends.ObjectPermissionBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]

    monkeypatch_abstract_generic()
    monkeypatch_djangotypes()
