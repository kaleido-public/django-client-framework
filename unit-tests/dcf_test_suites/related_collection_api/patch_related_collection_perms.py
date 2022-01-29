from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_dcf_user_model

User = get_dcf_user_model()


class TestPaginationPerms(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.brand = Brand.objects.create(name="brand")
        self.old_product = Product.objects.create(
            barcode="old_product", brand=self.brand
        )
        self.product = Product.objects.create(barcode="product")
        # self.products = [
        #     Product.objects.create(barcode=f"product_{i+1}", brand=self.brand)
        #     for i in range(100)
        # ]
        # self.br2 = Brand.objects.create(name="nike")
        # self.new_products = [
        #     Product.objects.create(barcode=f"product_{i+101}", brand=self.br2)
        #     for i in range(50)
        # ]

    def test_min_patch_perms(self) -> None:
        """Test minimum patch permission. Replaces the old product with new."""
        p.add_perms_shortcut(self.user, self.brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.old_product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        self.assertEqual(200, resp.status_code)
        self.product.refresh_from_db()
        self.old_product.refresh_from_db()
        self.assertEqual(self.product.brand, self.brand)
        self.assertIsNone(self.old_product.brand)

    def test_patch_parent_no_write(self) -> None:
        """If brand has no write perm, raise 403."""
        p.add_perms_shortcut(self.user, self.brand, "r", field_name="products")
        p.add_perms_shortcut(self.user, self.old_product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        self.assertEqual(403, resp.status_code)
        self.assertEqual(
            f"You have no ['write'] permission on brand({self.brand.id})'s products field.",
            resp.json(),
        )
        # unchanged
        self.product.refresh_from_db()
        self.old_product.refresh_from_db()
        self.assertEqual(self.old_product.brand, self.brand)
        self.assertIsNone(self.product.brand)

    def test_patch_parent_no_perm(self) -> None:
        """If brand has no write or read perm, raise 404."""
        p.add_perms_shortcut(self.user, self.old_product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        self.assertEqual(404, resp.status_code)
        self.assertEqual(
            f"Not Found: brand({self.brand.id})",
            resp.json(),
        )
        # unchanged
        self.product.refresh_from_db()
        self.old_product.refresh_from_db()
        self.assertEqual(self.old_product.brand, self.brand)
        self.assertIsNone(self.product.brand)

    def test_old_child_no_write(self) -> None:
        """What if User cannot write to the old child"""
        p.add_perms_shortcut(self.user, self.brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.old_product, "r", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "w", field_name="brand")
        resp = self.user_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        self.assertEqual(403, resp.status_code, resp.json())
        self.assertEqual(
            f"You have no ['write'] permission on product({self.old_product.id})'s brand field.",
            resp.json(),
        )
        # unchanged
        self.product.refresh_from_db()
        self.old_product.refresh_from_db()
        self.assertEqual(self.old_product.brand, self.brand)
        self.assertIsNone(self.product.brand)

    def test_new_child_no_write(self) -> None:
        """What if User cannot write to the new child"""
        p.add_perms_shortcut(self.user, self.brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.old_product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.product, "r", field_name="brand")
        resp = self.user_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        self.assertEqual(403, resp.status_code, resp.json())
        self.assertEqual(
            f"You have no ['write'] permission on product({self.product.id})'s brand field.",
            resp.json(),
        )
        # unchanged
        self.product.refresh_from_db()
        self.old_product.refresh_from_db()
        self.assertEqual(self.old_product.brand, self.brand)
        self.assertIsNone(self.product.brand)

    def test_new_child_no_perm(self) -> None:
        """What if User cannot write to the new child"""
        p.add_perms_shortcut(self.user, self.brand, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.old_product, "w", field_name="brand")
        resp = self.user_client.patch(
            f"/brand/{self.brand.id}/products",
            data=[self.product.id],
            format="json",
        )
        self.assertEqual(404, resp.status_code, resp.json())
        self.assertEqual(
            f"Not Found: product({self.product.id})",
            resp.json(),
        )
        # unchanged
        self.product.refresh_from_db()
        self.old_product.refresh_from_db()
        self.assertEqual(self.old_product.brand, self.brand)
        self.assertIsNone(self.product.brand)
