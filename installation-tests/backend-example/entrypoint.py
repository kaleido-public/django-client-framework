import json
import os
import shutil
from typing import Any
import unittest
from pathlib import Path
from subprocess import CompletedProcess, Popen, SubprocessError, run

from schema import Schema

PROJ = Path("/_out")


def debug() -> None:
    shell("sleep inf")


def shell(cmd: str, **kwargs: Any) -> CompletedProcess:
    print(f"+ {cmd}", flush=True)
    return run(cmd, shell=True, text=True, check=True, **kwargs)


def write_to_settings() -> None:
    settings = PROJ / "dcf_backend_example/settings.py"
    content = settings.read_text()
    new_content = f"""
import django_client_framework.settings

{content}

# added by entrypoint.py

REST_FRAMEWORK = {{}}
AUTHENTICATION_BACKENDS = []
INSTALLED_APPS += ["dcf_backend_example.common"]

django_client_framework.settings.install(
    INSTALLED_APPS,
    REST_FRAMEWORK,
    MIDDLEWARE,
    AUTHENTICATION_BACKENDS
)
"""
    settings.write_text(new_content)


def installation() -> None:
    for cmd in [
        "pip3 install /django_client_framework",
        f"django-admin startproject dcf_backend_example {PROJ.absolute()}",
        "mkdir dcf_backend_example/common",
        "python3 ./manage.py startapp common dcf_backend_example/common",
        "cp /_overwrite/apps.py dcf_backend_example/common/apps.py",
    ]:
        shell(cmd, cwd=PROJ)


def run_migration() -> None:
    for cmd in [
        "python3 ./manage.py makemigrations",
        "python3 ./manage.py migrate",
    ]:
        shell(cmd, cwd=PROJ)


def django_runserver() -> Popen:
    proc = Popen(
        "python3 ./manage.py runserver",
        shell=True,
        cwd=PROJ,
    )
    shell("wait-for-it localhost:8000")
    return proc


def create_objects() -> None:
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(PROJ.absolute())})
    shell(
        "python3 ./manage.py shell",
        cwd=PROJ,
        env=env,
        input="""
from dcf_backend_example.common.models import Product, Brand
nike = Brand.objects.create(id="123e4567-e89b-12d3-a456-426614174000", name="nike")
Product.objects.create(id="fcd12d1d-5f9f-40b9-a8b8-2d7b8d1f6f2f", barcode="xxyy", brand=nike)
""",
    )


def set_permissions() -> None:
    env = os.environ.copy()
    env.update({"PYTHONPATH": str(PROJ.absolute())})
    shell(
        "python3 ./manage.py shell",
        cwd=PROJ,
        env=env,
        input="""
from django_client_framework.permissions import reset_permissions
reset_permissions()
""",
    )


def clear() -> None:
    for content in PROJ.iterdir():
        if content.is_dir():
            shutil.rmtree(content.absolute())
        else:
            content.unlink()


def create_model() -> None:
    shutil.copyfile(
        "/_overwrite/models.py", PROJ / "dcf_backend_example/common/models.py"
    )


def add_routes() -> None:
    urls_py = PROJ / "dcf_backend_example/urls.py"
    content = urls_py.read_text()
    urls_py.write_text(
        f"""
import django_client_framework.api.urls
from django.urls import include

{content}

urlpatterns.append(path("", include(django_client_framework.api.urls)))
"""
    )


def zip_package() -> None:
    for cmd in [
        "tar -czvf /tmp/dcf-backend-example.tar.gz .",
        "mv /tmp/dcf-backend-example.tar.gz ./dcf-backend-example.tar.gz",
    ]:
        shell(cmd, cwd=PROJ)


class Test(unittest.TestCase):
    """
    The goal of this suite is to test for Django Client Framework's
    installation, making sure the instruction is up-to-date.
    """

    def query_product_list(self) -> None:
        result = shell("curl http://localhost:8000/product", capture_output=True)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        Schema(
            {
                "pages_count": 1,
                "objects_count": 1,
                "objects": [
                    {
                        "id": str,
                        "created_at": str,
                        "type": str,
                        "barcode": "xxyy",
                        "brand_id": str,
                    }
                ],
            },
            ignore_extra_keys=True,
        ).validate(response)

    def query_product(self) -> None:
        result = shell(
            "curl http://localhost:8000/product/fcd12d1d-5f9f-40b9-a8b8-2d7b8d1f6f2f",
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        Schema(
            {
                "id": str,
                "created_at": str,
                "type": str,
                "barcode": "xxyy",
                "brand_id": str,
            }
        ).validate(response)

    def query_product_brand(self) -> None:
        result = shell(
            "curl http://localhost:8000/product/fcd12d1d-5f9f-40b9-a8b8-2d7b8d1f6f2f/brand",
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        Schema(
            {
                "id": str,
                "created_at": str,
                "type": str,
                "name": "nike",
            }
        ).validate(response)

    def query_brand(self) -> None:
        result = shell(
            "curl http://localhost:8000/brand/123e4567-e89b-12d3-a456-426614174000",
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        Schema(
            {
                "id": str,
                "created_at": str,
                "type": str,
                "name": "nike",
            }
        ).validate(response)

    def query_brand_product_list(self) -> None:
        result = shell(
            "curl http://localhost:8000/brand/123e4567-e89b-12d3-a456-426614174000/products",
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        Schema(
            {
                "pages_count": 1,
                "objects_count": 1,
                "objects": [
                    {
                        "id": str,
                        "created_at": str,
                        "type": str,
                        "barcode": "xxyy",
                        "brand_id": str,
                    }
                ],
            },
            ignore_extra_keys=True,
        ).validate(response)

    def test_main(self) -> None:
        server = None

        try:
            clear()
            installation()
            write_to_settings()
            add_routes()
            create_model()
            run_migration()
            create_objects()
            set_permissions()
            server = django_runserver()
            self.query_product_list()
            self.query_product()
            self.query_product_brand()
            self.query_brand()
            self.query_brand_product_list()
            zip_package()

        except SubprocessError as err:
            exit(1)

        finally:
            if server:
                server.terminate()


if __name__ == "__main__":
    unittest.main()
