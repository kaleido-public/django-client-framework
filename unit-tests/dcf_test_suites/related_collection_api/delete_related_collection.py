from uuid import UUID

from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestDeleteRelatedCollection(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create(username="testuser", is_superuser=True)
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brand = Brand.objects.create(name="brand")
        self.products = [Product.objects.create(brand=self.brand) for i in range(3)]

    def test_delete_objects_success(self):
        assert Product.objects.count() == 3
        resp = self.superuser_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[str(p.id) for p in self.products],
            format="json",
        )
        self.assertEquals(resp.status_code, 200, resp.content)
        for p in self.products:
            p.refresh_from_db()
        self.assertIsNone(self.products[0].brand_id)
        self.assertIsNone(self.products[1].brand_id)
        self.assertIsNone(self.products[2].brand_id)
        self.assertEqual(
            3,
            Product.objects.count(),
            "Make sure this doesn't actually delete the objects! Just remove the relations.",
        )

    def test_delete_objects_none(self):
        """Deleting relations that doesn't actually exist."""
        resp = self.superuser_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[str(UUID(int=101)), str(UUID(int=102))],
            format="json",
        )
        self.assertEquals(resp.status_code, 200, resp.content)
        self.assertEquals(3, self.brand.products.count())
        self.assertEqual(
            3,
            Product.objects.count(),
            "Make sure this doesn't actually delete the objects! Just remove the relations.",
        )
