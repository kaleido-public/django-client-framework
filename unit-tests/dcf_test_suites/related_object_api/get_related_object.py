from dcf_test_app.models import Product
from dcf_test_app.models.brand import Brand
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class Test404(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.superuser = User.objects.create(username="testuser", is_superuser=True)
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brand = Brand.objects.create(name="brand")
        self.product = Product.objects.create(barcode="product", brand=self.brand)

    def test_404(self) -> None:
        self.product.brand = None
        self.product.save()
        resp = self.superuser_client.get(f"/product/{self.product.id}/brand")
        self.assertEqual(resp.status_code, 404)

    def test_get(self) -> None:
        resp = self.superuser_client.get(f"/product/{self.product.id}/brand")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertDictContainsSubset(
            {"id": str(self.brand.id), "name": "brand"}, resp.json()
        )

    def test_get_failed(self) -> None:
        resp = self.superuser_client.get("/product/2/brand")
        self.assertEqual(resp.status_code, 404)
