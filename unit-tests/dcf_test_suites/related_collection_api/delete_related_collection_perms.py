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
        self.product = Product.objects.create(barcode="prodcut", brand=self.brand)
        self.assertEqual(1, self.brand.products.count())

    def test_delete_min_perms(self):
        """Minimum permission required for a successful deletion"""
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        data = resp.json()
        self.assertEquals(200, resp.status_code)
        self.assertEquals(0, data.get("objects_count", ""), data)
        # product relation is now deleted
        self.product.refresh_from_db()
        self.assertIsNone(self.product.brand_id)
        self.assertEqual(0, self.brand.products.count())

    def test_delete_child_no_write(self):
        """When child has no write perm, delete should fail."""
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "r", field_name="brand")
        resp = self.user_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        data = resp.json()
        self.assertEquals(403, resp.status_code)
        self.assertEquals(
            f"You have no write permission on product({self.product.id})'s brand field.",
            data,
        )
        # product relation still exists
        self.product.refresh_from_db()
        self.assertEquals(self.product.brand_id, self.brand.id)
        self.assertEquals(1, self.brand.products.count())

    def test_delete_child_no_perm(self):
        """When child has no write perm, delete should fail. And if child has no
        read perm, should 404."""
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        resp = self.user_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        data = resp.json()
        self.assertEquals(404, resp.status_code, data)
        self.assertEquals(
            f"Not Found: product({self.product.id})",
            data,
        )
        # product relation still exists
        self.product.refresh_from_db()
        self.assertEquals(self.product.brand_id, self.brand.id)
        self.assertEquals(1, self.brand.products.count())

    def test_delete_parent_no_read(self):
        """Parent has no read perm, should succeed, but returns no data."""
        p.add_perms_shortcut(self.user, self.brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        data = resp.json()
        self.assertEquals(200, resp.status_code)
        self.assertDictEqual(
            {
                "detail": "Action was successful but you have no permission to view the result.",
            },
            data,
        )
        # product relation is now deleted
        self.product.refresh_from_db()
        self.assertIsNone(self.product.brand_id)
        self.assertEqual(0, self.brand.products.count())

    def test_delete_parent_no_write(self):
        """Parent has no write perm, should fail."""
        p.add_perms_shortcut(self.user, self.brand, "r", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        data = resp.json()
        self.assertEquals(403, resp.status_code)
        self.assertEquals(
            f"You have no write permission on brand({self.brand.id})'s products field.",
            data,
        )
        # product relation still exists
        self.product.refresh_from_db()
        self.assertEquals(self.product.brand_id, self.brand.id)
        self.assertEquals(1, self.brand.products.count())

    def test_delete_parent_no_perms(self):
        """
        Parent has no permissions, should fail, and since no read perm, returns
        404.
        """
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.delete(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        data = resp.json()
        self.assertEquals(404, resp.status_code)
        self.assertEquals(
            f"Not Found: brand({self.brand.id})",
            data,
        )
        # product relation still exists
        self.product.refresh_from_db()
        self.assertEquals(self.product.brand_id, self.brand.id)
        self.assertEquals(1, self.brand.products.count())
