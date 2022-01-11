from uuid import UUID

from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestPatch(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.superuser = User.objects.create(username="testuser", is_superuser=True)
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brand = Brand.objects.create(name="brand")
        self.products = [
            Product.objects.create(barcode=f"product_{i+1}", brand=self.brand)
            for i in range(5)
        ]

    def test_patch_objects_all(self) -> None:
        assert self.brand.products.count() == 5
        self.superuser_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.products[0].id, self.products[1].id],
            format="json",
        )
        self.assertEqual(self.brand.products.count(), 2)

    def test_patch_objects_unlink_all(self) -> None:
        assert self.brand.products.count() == 5
        resp = self.superuser_client.patch(
            f"/brand/{self.brand.id}/products", data=[], format="json"
        )
        self.assertEquals(0, len(resp.json()["objects"]))
        self.assertEqual(self.brand.products.count(), 0)

    def test_patch_objects_invalid_key(self) -> None:
        assert self.brand.products.count() == 5
        resp = self.superuser_client.patch(
            f"/brand/{self.brand.id}/products", data=[UUID(int=200)], format="json"
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(self.brand.products.count(), 5)
