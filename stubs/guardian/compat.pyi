from typing import Any

from django.conf.urls import handler404 as handler404
from django.conf.urls import handler500 as handler500
from django.conf.urls import include as include
from django.contrib.auth import get_user_model as get_user_model
from django.contrib.auth.models import AnonymousUser as AnonymousUser
from django.contrib.auth.models import Group as Group
from django.contrib.auth.models import Permission as Permission

user_model_label: Any
