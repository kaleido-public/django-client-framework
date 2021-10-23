from subprocess import run

from django.core.cache import cache
from django.http import HttpResponse
from subapp.models import Brand, Product

from django_client_framework.permissions import (
    add_perms_shortcut,
    default_groups,
    reset_permissions,
)


def clear(request):
    shell("python3 manage.py flush --no-input")
    cache.clear()
    reset_permissions([Product, Brand])
    add_perms_shortcut(default_groups.anyone, Product, "rwcd")
    add_perms_shortcut(default_groups.anyone, Brand, "rwcd")
    return HttpResponse("Successfully deleted all.")


def shell(cmd, **kwargs):
    print(f"+ {cmd}", flush=True)
    return run(
        cmd,
        shell=True,
        text=True,
        check=True,
        **kwargs,
    )
