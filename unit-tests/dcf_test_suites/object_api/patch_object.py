from uuid import UUID

import schema
from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.permissions import default_users, reset_permissions


class TestPatchObject(TestCase):
    def setUp(self) -> None:
        reset_permissions()
        self.superuser = default_users.root
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.pr = Product.objects.create()
        self.br = Brand.objects.create()

    def test_patch_successful(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.pr.id}",
            {"barcode": "newbarcode", "brand_id": str(self.br.id)},
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.pr.refresh_from_db()
        self.assertEqual(self.pr.barcode, "newbarcode")
        self.assertEqual(self.pr.brand, self.br)

    def test_patch_invalid_fk(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.pr.id}", {"barcode": "newbarcode", "brand_id": UUID(int=3)}
        )
        self.assertEqual(400, resp.status_code, resp.content)
        self.assertContains(
            resp, "does not exist", status_code=400, msg_prefix=str(resp.content)
        )

    def test_patch_invalid_keys(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.pr.id}",
            {"xxxxx": "product_2", "brand_id": str(self.br.id)},
        )
        data = resp.json()
        schema.Schema(
            {
                "code": "validation_error",
                "message": str,
                "fields": {
                    "xxxxx": str,
                },
                "non_field": str,
            },
        ).validate(data)
