from uuid import UUID

from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestPostCollection(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create_superuser(username="testuser")
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brands = [Brand.objects.create(name=f"name_{i+1}") for i in range(5)]

    def test_post_without_id(self):
        """POST without specifying an ID. A new UUID should be automatically assigned."""
        assert Product.objects.count() == 0
        resp = self.superuser_client.post("/product", {})
        self.assertEqual(201, resp.status_code, resp.content)
        self.assertEquals(1, Product.objects.count())

    def test_post_blank_id(self):
        """Blank ID is treated as without specifying an ID."""
        assert Product.objects.count() == 0
        for count in range(1, 3):
            resp = self.superuser_client.post("/product", {"id": ""})
            self.assertEqual(201, resp.status_code, resp.content)
            self.assertEquals(count, Product.objects.count())

    def test_post_with_invalid_id(self):
        assert Product.objects.count() == 0

        resp = self.superuser_client.post("/product", {"id": "1"})
        self.assertEqual(400, resp.status_code)
        self.assertEqual("invalid", resp.json()["id"][0]["code"])

        resp = self.superuser_client.post("/product", {"id": 1})
        self.assertEqual(400, resp.status_code)
        self.assertEqual("invalid", resp.json()["id"][0]["code"])

        self.assertEquals(0, Product.objects.count())

    def test_post_with_duplicate_id(self):
        self.assertEquals(0, Product.objects.count())
        resp = self.superuser_client.post("/product", {"id": str(UUID(int=1))})
        self.assertEqual(201, resp.status_code, resp.content)
        self.assertEquals(1, Product.objects.count())
        resp = self.superuser_client.post("/product", {"id": str(UUID(int=1))})
        self.assertEqual(400, resp.status_code, resp.content)
        # self.assertLi(400, resp.json(), resp.content)
        self.assertEquals(1, Product.objects.count())

    def test_post_invalid_field(self):
        resp = self.superuser_client.post("/product", {"xxxxxx": "test_brand"})
        self.assertEquals(0, Product.objects.count())
        self.assertEqual(400, resp.status_code)
        data = resp.json()
        self.assertEqual("invalid", data["xxxxxx"][0]["code"])

    def test_post_invalid_fk(self):
        self.assertEquals(0, Product.objects.count())
        resp = self.superuser_client.post(
            "/product",
            {"barcode": "unique", "brand_id": UUID(int=200)},
        )
        self.assertEqual(400, resp.status_code)
        self.assertEquals(0, Product.objects.count())
        self.assertDictContainsSubset(
            {"code": "does_not_exist"},
            resp.json()["brand_id"][0],
            resp.json(),
        )
