from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django_client_framework import permissions as p


class TestPaginationPerms(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.brand = Brand.objects.create(name="brand")
        self.products = [
            Product.objects.create(barcode=f"product_{i+1}", brand=self.brand)
            for i in range(100)
        ]
        self.br2 = Brand.objects.create(name="nike")
        self.new_products = [
            Product.objects.create(barcode=f"product_{i+101}", brand=self.br2)
            for i in range(50)
        ]

    def test_delete_no_permissions(self):
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_delete_incorrect_parent_permissions(self):
        p.add_perms_shortcut(self.user, Brand, "r", field_name="products")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_delete_correct_parent_perms(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_delete_correct_parent_incorrect_reverse_field_perms(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, Product, "r", field_name="brand")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        self.assertEquals(404, resp.status_code)

    def test_delete_correct_parent_incorrect_reverse_field_perms_ver_2(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        self.assertEquals(403, resp.status_code)

    def test_delete_correct_parent_and_reverse_perms(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, Product, "w")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(True, data["success"])
        self.assertEquals(None, Product.objects.get(id=99).brand_id)
        self.assertEquals(99, Product.objects.filter(brand_id=1).count())

    def test_delete_correct_parent_and_reverse_perms_ver_2(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(None, Product.objects.get(id=99).brand_id)
        self.assertTrue(data["success"])
        self.assertEquals(99, Product.objects.filter(brand_id=1).count())

    def test_delete_correct_parent_and_reverse_perms_with_correct_read_perms(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, Brand, "r")
        p.add_perms_shortcut(self.user, Product, "r")
        p.add_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(50, len(data["objects"]))
        self.assertDictEqual(
            data["objects"][0], {"id": 1, "barcode": "product_1", "brand_id": 1}
        )
        self.assertEquals(None, Product.objects.get(id=99).brand_id)
        self.assertEquals(99, Product.objects.filter(brand_id=1).count())

    def test_delete_correct_parent_and_reverse_perms_with_correct_read_perms_v2(self):
        p.add_perms_shortcut(
            self.user, Brand.objects.get(id=1), "wr", field_name="products"
        )
        p.add_perms_shortcut(self.user, Product.objects.filter(id=10), "r")
        p.add_perms_shortcut(self.user, Product.objects.filter(id=9), "r")
        p.add_perms_shortcut(self.user, Product.objects.filter(id=11), "r")
        p.add_perms_shortcut(
            self.user, Product.objects.filter(id=99), "w", field_name="brand"
        )
        resp = self.user_client.delete(
            "/brand/1/products", data=[99], content_type="application/json"
        )
        data = resp.json()
        self.assertEquals(3, len(data["objects"]))
        self.assertDictEqual(
            data["objects"][0], {"id": 9, "barcode": "product_9", "brand_id": 1}
        )
        self.assertEquals(None, Product.objects.get(id=99).brand_id)
        self.assertEquals(99, Product.objects.filter(brand_id=1).count())
