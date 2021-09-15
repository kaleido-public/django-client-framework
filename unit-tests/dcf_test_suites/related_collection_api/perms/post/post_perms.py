from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from dcf_test_app.models import Product
from dcf_test_app.models import Brand
from django_client_framework import permissions as p


class TestPostPerms(TestCase):
    """POSTing to the related collection api creates new relations."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.brand = Brand.objects.create(name="brand")
        self.product = Product.objects.create(barcode="product")

    def test_full_permission_post(self):
        """
        Post with read and field write permissions.
        """
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "r")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        data = resp.json()
        self.assertEquals(200, resp.status_code)
        self.product.refresh_from_db()
        self.assertEquals(1, self.product.brand_id)
        self.assertEquals(1, data["total"])
        self.assertDictContainsSubset({"id": self.product.id}, data["objects"][0])

    def test_no_child_read(self):
        """
        If product has no read permission, post should be successful but hidden.
        """
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        data = resp.json()
        self.product.refresh_from_db()
        self.assertEquals(1, self.product.brand_id)  # product is actually updated
        self.assertEqual(1, self.brand.products.count())  # product is actually updated
        self.assertEquals(200, resp.status_code)
        self.assertEquals(0, data["total"])

    def test_no_child_write(self):
        """
        Has no product write permission, post should be 403.
        """
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "r")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        data = resp.json()
        self.assertEquals(403, resp.status_code)
        self.assertIsNone(self.product.brand_id)  # product is not updated
        self.assertEqual(0, self.brand.products.count())  # product is not updated
        self.assertEquals(
            data, "You have no write permission on product(1)'s brand field."
        )

    def test_no_child_perm(self):
        """
        Has no product read / write permission, post should be 404.
        """
        p.add_perms_shortcut(self.user, self.brand, "rw", field_name="products")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        data = resp.json()
        self.assertEquals(404, resp.status_code)
        self.assertIsNone(self.product.brand_id)  # product is not updated
        self.assertEqual(0, self.brand.products.count())  # product is not updated
        self.assertEquals(data, "Not Found: product(1)")

    def test_no_parent_write(self):
        """
        Has no brand write perm, should 403.
        """
        p.add_perms_shortcut(self.user, self.brand, "r", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "r")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        data = resp.json()
        self.assertEquals(403, resp.status_code)
        self.assertEquals(
            data,
            "You have no write permission on brand(1)'s products field.",
        )
        self.assertIsNone(self.product.brand_id)  # product is not updated
        self.assertEqual(0, self.brand.products.count())  # product is not updated

    def test_no_parent_read(self):
        """
        Has no brand read perm, but since can write to brand, the response is
        200.
        """
        p.add_perms_shortcut(self.user, self.brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "r")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        self.assertEquals(200, resp.status_code)
        data = resp.json()
        self.assertEqual(
            data["detail"],
            "Action was successful but you have no permission to view the result.",
        )
        self.product.refresh_from_db()
        self.assertEquals(1, self.product.brand_id)  # product is actually updated
        self.assertEqual(1, self.brand.products.count())  # product is actually updated

    def test_no_parent_perm(self):
        """
        Has no brand perm, should 404.
        """
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "r")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        self.assertEquals(404, resp.status_code)
        self.assertEqual(f"Not Found: brand({self.brand.id})", resp.json())
        self.assertIsNone(self.product.brand_id)  # product is not updated
        self.assertEqual(0, self.brand.products.count())  # product is not updated

    def test_post_no_permissions(self):
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        self.assertEquals(404, resp.status_code)

    def test_post_correct_parent_perms(self):
        p.add_perms_shortcut(self.user, Brand, "w", field_name="products")
        resp = self.user_client.post(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            content_type="application/json",
        )
        self.assertEquals(404, resp.status_code)
