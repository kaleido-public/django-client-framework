from uuid import UUID

from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestPost(TestCase):
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

    def test_post_related_success(self) -> None:
        """POST-ing adds a relation."""
        self.brand.products.set(self.products[:3])
        assert self.brand.products.count() == 3
        resp = self.superuser_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.products[3].id, self.products[4].id],
            format="json",
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.assertEquals(5, len(resp.json()["objects"]))

    def test_post_related_failure(self) -> None:
        assert self.brand.products.count() == 5
        resp = self.superuser_client.post(
            f"/brand/{self.brand.id}/products",
            data=[UUID(int=160), UUID(int=170)],
            format="json",
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            self.brand.products.count(),
            5,
            "The brand's product count shouldn't have changed.",
        )

    def test_post_related_partial_failure(self) -> None:
        """What if half the IDs are correct but the other half is invalid?"""
        self.brand.products.set(self.products[:3])
        assert self.brand.products.count() == 3
        resp = self.superuser_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.products[4].id, UUID(int=180)],
            format="json",
        )
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(
            self.brand.products.count(),
            3,
            "The brand's product count shouldn't have changed.",
        )
