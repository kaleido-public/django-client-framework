from uuid import UUID

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
        self.brands = [
            Brand.objects.create(id=UUID(int=i), name=f"brand_{i}", priority=i)
            for i in range(100)
        ]
        self.products = [
            Product.objects.create(
                id=UUID(int=i),
                barcode=f"product_{i}",
                brand=self.brands[i] if i % 2 == 0 else None,
                priority=i,
            )
            for i in range(100)
        ]
        Product.objects.create(barcode="product_100", brand=None, priority=100)

    def test_list(self):
        resp = self.superuser_client.get("/product?_order_by=priority")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 101},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[0].id),
                "barcode": "product_0",
                "brand_id": str(self.brands[0].id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {"id": str(self.products[1].id), "barcode": "product_1", "brand_id": None},
            objects[1],
        )

    def test_distict_result(self):
        """
        When filtering with a query that results in a left-join operation, make
        sure the results are distict.
        """
        brand = Brand.objects.get(id=1)
        brand.products.set(Product.objects.filter(id__in=[1, 2, 3]))
        result = Brand.objects.filter(products__in=[1, 2, 3])
        self.assertEqual(3, len(result))
        resp = self.superuser_client.get(
            f"/brand?products__in[]={self.products[1].id},{self.products[2].id},{self.products[3].id}"
        )
        data = resp.json()
        self.assertEqual(1, data["objects_count"], data)

    def test_list_next_page(self):
        resp = self.superuser_client.get("/product?_page=2&_order_by=priority")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 2, "limit": 50, "objects_count": 101},
            data,
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 50)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[50].id),
                "barcode": "product_50",
                "brand_id": str(self.brands[50].id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[51].id),
                "barcode": "product_51",
                "brand_id": None,
            },
            objects[1],
        )

    def test_page_with_limit(self):
        resp = self.superuser_client.get(
            "/product?_page=3&_limit=10&_order_by=priority"
        )
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"page": 3, "limit": 10, "objects_count": 101}, data
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[20].id),
                "barcode": "product_20",
                "brand_id": str(self.brands[20].id),
                "priority": 20,
            },
            objects[0],
            data,
        )

    def test_key_name_single(self):
        resp = self.superuser_client.get("/product?barcode__exact=product_21")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 1}, data
        )
        self.assertEqual(len(objects), 1)
        self.assertDictContainsSubset(
            {"barcode": "product_21"},
            objects[0],
        )

    def test_key_name_multiple(self):
        resp = self.superuser_client.get(
            f"/product?barcode__exact=product_99&id__exact={self.products[99].id}"
        )
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 1}, data
        )
        self.assertEqual(len(objects), 1)
        self.assertDictContainsSubset(
            {
                "id": str(self.products[99].id),
                "barcode": "product_99",
            },
            objects[0],
        )

    def test_extend_past_page(self):
        resp = self.superuser_client.get("/product?_page=4")
        data = resp.json()
        self.assertDictContainsSubset({"message": "Invalid page."}, data)

    def test_extend_past_page_with_limit(self):
        resp = self.superuser_client.get("/product?_limit=40&_page=4")
        data = resp.json()
        self.assertDictContainsSubset({"message": "Invalid page."}, data)

    def test_key_name_array_filled_empty(self):
        resp = self.superuser_client.get(
            "/product?barcode__in[]=product_121&barcode__in[]=product_122"
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 0}, data
        )
        self.assertEqual(len(data["objects"]), 0)

    def test_key_name_array_but_empty(self):
        resp = self.superuser_client.get("/product?id__in[]=")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 0}, data, data
        )
        self.assertEqual(len(data["objects"]), 0)

    def test_key_name_array(self):
        resp = self.superuser_client.get(
            "/product?barcode__in[]=product_21&barcode__in[]=product_22&_order_by=priority"
        )
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 2}, data
        )
        self.assertEqual(len(data["objects"]), 2)
        self.assertDictContainsSubset({"barcode": "product_21"}, objects[0])
        self.assertDictContainsSubset({"barcode": "product_22"}, objects[1])

    def test_invalid_key(self):
        resp = self.superuser_client.get("/product?xxxxxx=product_21")

        self.assertEqual(400, resp.status_code)

    def test_positive_order(self):
        resp = self.superuser_client.get("/product?_order_by=priority")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 101}, data
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[0].id),
                "barcode": "product_0",
                "priority": 0,
                "brand_id": str(self.brands[0].id),
            },
            objects[0],
        )
        self.assertDictContainsSubset(
            {
                "id": str(self.products[2].id),
                "barcode": "product_2",
                "priority": 2,
                "brand_id": str(self.brands[2].id),
            },
            objects[2],
        )

    def test_negative_order(self):
        resp = self.superuser_client.get("/product?_order_by=-priority")
        data = resp.json()
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 101}, data
        )
        self.assertDictContainsSubset({"priority": 100}, objects[0])
        self.assertDictContainsSubset({"priority": 99}, objects[1])

    def test_order_multiple_keys_positive(self):
        resp = self.superuser_client.get(
            "/product", {"_order_by": "-barcode,priority", "_limit": 3}
        )
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(3, len(objects))
        self.assertDictContainsSubset({"barcode": "product_99"}, objects[0])
        self.assertDictContainsSubset({"barcode": "product_98"}, objects[1])
        self.assertDictContainsSubset({"barcode": "product_97"}, objects[2])

    def test_order_multiple_keys_negative(self):
        resp = self.superuser_client.get(
            "/product", {"_order_by": "-barcode,-priority", "_limit": 3}
        )
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(3, len(objects))
        self.assertDictContainsSubset(
            {"barcode": "product_99"},
            objects[0],
        )
        self.assertDictContainsSubset(
            {"barcode": "product_98"},
            objects[1],
        )
        self.assertDictContainsSubset(
            {"barcode": "product_97"},
            objects[2],
        )

    def test_order_malformed(self):
        resp = self.superuser_client.get("/product?_order_by=xxxxx")
        self.assertEquals(400, resp.status_code)
