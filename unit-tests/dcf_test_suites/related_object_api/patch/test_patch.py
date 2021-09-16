from dcf_test_app.models import Brand, Product
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class TestRetrieve(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brands = [Brand.objects.create(name=f"brand_{i+1}") for i in range(20)]
        self.products = [
            Product.objects.create(barcode=f"product_{i+1}", brand=self.brands[i])
            for i in range(20)
        ]

    def test_patch_success(self):
        resp = self.superuser_client.patch(
            "/product/1/brand", data=12, content_type="application/json"
        )
        self.assertEqual(12, Product.objects.get(id=1).brand_id, resp.json())

    def test_patch_success_string(self):
        resp = self.superuser_client.patch(
            "/product/1/brand", data="12", content_type="application/json"
        )
        self.assertEqual(12, Product.objects.get(id=1).brand_id, resp.json())

    def test_patch_failed_invalid_fk(self):
        resp = self.superuser_client.patch(
            "/product/1/brand", data=23, content_type="application/json"
        )
        data = resp.json()
        self.assertDictEqual(data, {"detail": "Not Found: Brand (23)"})

    def test_patch_failed_multiple_ids(self):
        resp = self.superuser_client.patch(
            "/product/1/brand", data=[23, 24], content_type="application/json"
        )
        data = resp.json()
        self.assertDictEqual(
            data,
            {
                "non_field_error": "Expected an object pk in the request body, but received list: [23, 24]"
            },
        )
