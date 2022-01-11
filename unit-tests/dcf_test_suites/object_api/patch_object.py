from uuid import UUID

from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestPatchObject(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.superuser = User.objects.create(username="testuser", is_superuser=True)
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
        data = resp.json()
        self.assertEquals("does_not_exist", data["brand_id"][0]["code"])

    def test_patch_invalid_keys(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.pr.id}",
            {"xxxxx": "product_2", "brand_id": str(self.br.id)},
        )
        data = resp.json()
        self.assertEqual("invalid", data["xxxxx"][0]["code"])
