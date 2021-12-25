from django.conf.urls import handler404 as handler404, handler500 as handler500, include as include
from django.contrib.auth import get_user_model as get_user_model
from django.contrib.auth.models import AnonymousUser as AnonymousUser, Group as Group, Permission as Permission
from typing import Any

user_model_label: Any
