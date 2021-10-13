from dcf_test_app.models import Brand, Product
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p


class TestPatchPerms(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

    def test_patch_no_permission(self):
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.assertEqual(404, resp.status_code)

    def test_patch_incorrect_permission(self):
        p.add_perms_shortcut(self.user, Product, "rcd")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.assertEqual(403, resp.status_code)

    def test_patch_only_parent_permission(self):
        p.add_perms_shortcut(self.user, Product, "w")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.assertEqual(404, resp.status_code)

    def test_patch_parent_but_incorrect_related_perms(self):
        p.add_perms_shortcut(self.user, Product, "w")
        p.add_perms_shortcut(self.user, Brand, "rcd")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.assertEqual(403, resp.status_code)

    def test_correct_patch_perms_no_read(self):
        p.add_perms_shortcut(self.user, Product, "w")
        p.add_perms_shortcut(self.user, Brand, "w")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.pr1.refresh_from_db()
        self.assertEqual(self.br2, self.pr1.brand)
        self.assertEqual(resp.status_code, 200)
        self.assertDictContainsSubset(
            {
                "detail": "Action was successful but you have no permission to view the result."
            },
            resp.json(),
        )

    def test_correct_patch_perms_no_read_v2(self):
        p.add_perms_shortcut(self.user, Product, "w")
        p.add_perms_shortcut(self.user, Brand, "wr")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.pr1.refresh_from_db()
        self.assertEqual(self.br2, self.pr1.brand)
        self.assertEqual(resp.status_code, 200)
        self.assertDictContainsSubset(
            {
                "detail": "Action was successful but you have no permission to view the result."
            },
            resp.json(),
        )

    def test_correct_patch_perms_can_read(self):
        p.add_perms_shortcut(self.user, Brand, "rw")
        p.add_perms_shortcut(self.user, Product, "rw")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.pr1.refresh_from_db()
        self.assertEqual(self.br2, self.pr1.brand)
        self.assertDictContainsSubset({"id": str(self.br2.id)}, resp.json())

    def test_correct_patch_perms_can_read_v2(self):
        p.add_perms_shortcut(self.user, self.pr1, "rw")
        p.add_perms_shortcut(self.user, self.br1, "w")
        p.add_perms_shortcut(self.user, self.br2, "rw")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.pr1.refresh_from_db()
        self.assertEqual(self.br2, self.pr1.brand)
        self.assertDictContainsSubset({"id": str(self.br2.id)}, resp.json())

    def test_correct_patch_perms_can_read_v3(self):
        p.add_perms_shortcut(self.user, self.pr1, "rw", field_name="brand")
        p.add_perms_shortcut(self.user, self.br1, "w", field_name="products")
        p.add_perms_shortcut(self.user, self.br2, "r")
        p.add_perms_shortcut(self.user, self.br2, "w", field_name="products")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}/brand",
            data=self.br2.id,
            format="json",
        )
        self.pr1.refresh_from_db()
        self.assertEqual(self.br2, self.pr1.brand)
        self.assertDictContainsSubset({"id": str(self.br2.id)}, resp.json())

    def test_assign_from_null(self):
        """PATCH Product.brand from None to existing"""
        product = Product.objects.create()
        p.add_perms_shortcut(self.user, product, "r")
        p.add_perms_shortcut(self.user, product, "w", field_name="brand")
        brand = Brand.objects.create(name="new branch")
        p.add_perms_shortcut(self.user, brand, "r")
        p.add_perms_shortcut(self.user, brand, "w", field_name="products")
        resp = self.user_client.patch(
            f"/product/{product.id}/brand",
            data=brand.id,
            format="json",
        )
        product.refresh_from_db()
        self.assertEqual(product.brand, brand, resp.json())
