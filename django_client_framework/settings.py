def monkeypatch_djangotypes():
    # Monkey patch for django-types
    # https://github.com/sbdchd/django-types
    # in settings.py
    from django.db.models import ForeignKey
    from django.db.models.manager import BaseManager
    from django.db.models.query import QuerySet

    # NOTE: there are probably other items you'll need to monkey patch depending on
    # your version.
    for cls in [QuerySet, BaseManager, ForeignKey]:
        cls.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore [attr-defined]


def monkeypatch_abstract_generic():
    # Monkey patch for django-types See
    # https://github.com/typeddjango/django-stubs/issues/299 in settings.py
    from typing import Generic
    from django.db.migrations.state import ModelState

    _original = ModelState.render

    def _new(self, apps):
        self.bases = tuple(base for base in self.bases if base is not Generic)  # type: ignore
        return _original(self, apps)

    ModelState.render = _new  # type: ignore


monkeypatch_abstract_generic()


def install(
    INSTALLED_APPS,
    REST_FRAMEWORK,
    MIDDLEWARE,
    AUTHENTICATION_BACKENDS,
):
    INSTALLED_APPS += [
        "rest_framework",
        "guardian",
        "django_client_framework.apps.DefaultApp",
    ]
    MIDDLEWARE += [
        "django_client_framework.exceptions.handlers.ConvertAPIExceptionToJsonResponse",
        "django_currentuser.middleware.ThreadLocalUserMiddleware",
    ]
    REST_FRAMEWORK[
        "EXCEPTION_HANDLER"
    ] = "django_client_framework.exceptions.handlers.dcf_exception_handler"
    AUTHENTICATION_BACKENDS += [
        "guardian.backends.ObjectPermissionBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]

    monkeypatch_djangotypes()
    monkeypatch_abstract_generic()
