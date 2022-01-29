from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.permissions import default_users


class TestObject(TestCase):
    def setUp(self) -> None:
        self.superuser = default_users.root
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.br = Brand.objects.create(name="brand")
        self.pr1 = Product.objects.create(barcode="product_1", brand=self.br)
        self.pr2 = Product.objects.create(barcode="product_2")

    def test_get_1(self) -> None:
        resp = self.superuser_client.get(f"/product/{self.pr1.id}")
        data = resp.json()
        self.assertDictContainsSubset(
            {
                "id": str(self.pr1.id),
                "barcode": "product_1",
                "brand_id": str(self.br.id),
            },
            data,
        )

    def test_get_2(self) -> None:
        resp = self.superuser_client.get(f"/product/{self.pr2.id}")
        data = resp.json()
        self.assertDictContainsSubset(
            {"id": str(self.pr2.id), "barcode": "product_2", "brand_id": None}, data
        )
