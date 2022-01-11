from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestPagination(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superuser = User.objects.create(username="testuser", is_superuser=True)
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brand = Brand.objects.create(name="brand")
        self.products = [
            Product.objects.create(barcode=f"product_{i}", brand=self.brand, priority=i)
            for i in range(100)
        ]
        self.br2 = Brand.objects.create(name="nike")
        self.products += [
            Product.objects.create(
                barcode=f"product_{i+100}", brand=self.br2, priority=i + 100
            )
            for i in range(50)
        ]

    def test_list(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_order_by=priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 100},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[0].id),
                "barcode": "product_0",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[1].id),
                "barcode": "product_1",
                "brand_id": str(self.brand.id),
            },
            objects[1],
        )

    def test_list_next_page(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_page=2&_order_by=priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 2, "limit": 50, "objects_count": 100},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[50].id),
                "barcode": "product_50",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[51].id),
                "barcode": "product_51",
                "brand_id": str(self.brand.id),
            },
            objects[1],
        )

    def test_page_with_limit(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_page=3&_limit=30&_order_by=priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 3, "limit": 30, "objects_count": 100}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 30)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[60].id),
                "barcode": "product_60",
                "brand_id": str(self.brand.id),
                "priority": 60,
            },
            objects[0],
        )

    def test_limit_without_page(self):
        resp = self.superuser_client.get(
            f"/brand/{self.br2.id}/products?_limit=5&_order_by=priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 5, "objects_count": 50}, data
        )
        objects = data["objects"]
        self.assertDictContainsSubset(
            {
                "id": str(self.products[100].id),
                "barcode": "product_100",
                "brand_id": str(self.br2.id),
            },
            objects[0],
        )

    def test_extend_past_page(self):
        resp = self.superuser_client.get(f"/brand/{self.br2.id}/products?_page=2")
        data = resp.json()
        self.assertDictContainsSubset(
            {"general_errors": ["Invalid page."]},
            data,
            resp.content,
        )

    def test_extend_past_page_with_limit(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_limit=20&_page=40"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"general_errors": ["Invalid page."]},
            data,
            resp.content,
        )

    def test_key_single_empty(self):
        resp = self.superuser_client.get(f"/brand/{self.br2.id}/products?barcode=xxx")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 0}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 0)

    def test_key_single_filled(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?barcode=product_60"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 1}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 1)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[60].id),
                "barcode": "product_60",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )

    def test_key_multiple_filled(self):
        resp = self.superuser_client.get(
            f"/brand/{self.br2.id}/products?barcode=product_101&brand_id={self.br2.id}"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 1}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 1)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[101].id),
                "barcode": "product_101",
                "brand_id": str(self.br2.id),
            },
            objects[0],
        )

    def test_key_multiple_empty(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?barcode=product_102&brand_id={self.brand.id}"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 0}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 0)

    def test_key_array_filled(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?barcode__in[]=product_10,product_11&_order_by=priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 2}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 2)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[10].id),
                "barcode": "product_10",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )

    def test_key_array_empty(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?barcode__in[]=product_101,product_111"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 0}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 0)

    def test_order_positive(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_order_by=priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 100}, data
        )
        objects = data["objects"]
        self.assertDictContainsSubset(
            {
                "id": str(self.products[0].id),
                "barcode": "product_0",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[1].id),
                "barcode": "product_1",
                "brand_id": str(self.brand.id),
            },
            objects[1],
        )

    def test_order_negative(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_order_by=-priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 100}, data
        )
        objects = data["objects"]
        self.assertDictContainsSubset(
            {
                "id": str(self.products[99].id),
                "barcode": "product_99",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[98].id),
                "barcode": "product_98",
                "brand_id": str(self.brand.id),
            },
            objects[1],
        )

    def test_order_page(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_order_by=barcode&_page=2"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 2, "limit": 50, "objects_count": 100}, data
        )
        objects = data["objects"]
        self.assertDictContainsSubset(
            {
                "id": str(self.products[54].id),
                "barcode": "product_54",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[55].id),
                "barcode": "product_55",
                "brand_id": str(self.brand.id),
            },
            objects[1],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[56].id),
                "barcode": "product_56",
                "brand_id": str(self.brand.id),
            },
            objects[2],
        )

    # error: multiple keys not working
    def test_order_multiple_keys(self):
        resp = self.superuser_client.get(
            f"/brand/{self.brand.id}/products?_order_by=barcode,brand,priority"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 100}, data
        )
        objects = data["objects"]
        self.assertDictContainsSubset(
            {
                "id": str(self.products[0].id),
                "barcode": "product_0",
                "brand_id": str(self.brand.id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[1].id),
                "barcode": "product_1",
                "brand_id": str(self.brand.id),
            },
            objects[1],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[10].id),
                "barcode": "product_10",
                "brand_id": str(self.brand.id),
            },
            objects[2],
        )
