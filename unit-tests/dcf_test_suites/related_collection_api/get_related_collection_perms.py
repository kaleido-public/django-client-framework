from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_user_model


class TestPaginationPerms(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.brand = Brand.objects.create(name="brand")
        self.products = [
            Product.objects.create(
                barcode=f"product_{i+1}",
                brand=self.brand,
                priority=i,
            )
            for i in range(100)
        ]

    def test_no_permissions_get(self):
        resp = self.user_client.get(f"/brand/{self.brand.id}/products")
        self.assertEquals(404, resp.status_code, resp.content)

    # error: needs to only show the "products" that have read-level permission, right now shows all
    def test_only_parent_permissions_get(self):
        p.add_perms_shortcut(self.user, Brand, "r", field_name="products")
        resp = self.user_client.get(f"/brand/{self.brand.id}/products")
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(len(objects), 0)

    # error: need to only show product_3
    def test_only_parent_permissions_get_2(self):
        p.add_perms_shortcut(self.user, Brand, "r", field_name="products")
        p.add_perms_shortcut(self.user, self.products[2], "r")
        resp = self.user_client.get(f"/brand/{self.brand.id}/products")
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(len(objects), 1)
        self.assertDictContainsSubset({"barcode": "product_3"}, objects[0])

    # error: need to return no objects
    def test_correct_parent_incorrect_reverse_perms_get(self):
        p.add_perms_shortcut(self.user, Brand, "r", field_name="products")
        p.add_perms_shortcut(self.user, Product, "wcd")
        resp = self.user_client.get(f"/brand/{self.brand.id}/products")
        data = resp.json()
        self.assertEquals(0, data["total"])
        self.assertEquals(len(data["objects"]), 0)

    def test_get_with_object_level_perm(self):
        p.add_perms_shortcut(self.user, Brand, "r", field_name="products")
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get(
            f"/brand/{self.brand.id}/products?_order_by=priority"
        )
        self.assertEqual(200, resp.status_code, resp.content)
        data = resp.json()
        objects = data["objects"]
        self.assertEquals(50, len(objects))
        self.assertDictContainsSubset(
            {"barcode": "product_1"},
            objects[0],
        )
        self.assertDictContainsSubset(
            {"barcode": "product_50"},
            objects[49],
        )
