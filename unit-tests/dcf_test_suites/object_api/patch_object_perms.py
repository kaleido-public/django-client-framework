from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_dcf_user_model
from django_client_framework.permissions import reset_permissions

User = get_dcf_user_model()


class TestPatchPerms(TestCase):
    def setUp(self) -> None:
        reset_permissions()
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

    def test_patch_no_permissions(self) -> None:
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {"barcode": "p1"},
            format="json",
        )
        self.assertEquals(404, resp.status_code)

    def test_patch_incorrect_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "rcd")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {"barcode": "p1"},
            format="json",
        )
        self.assertEquals(403, resp.status_code)

    def test_patch_wrong_field(self) -> None:
        p.add_perms_shortcut(self.user, Product, "w", field_name="brand_id")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {"barcode": "xxxxx"},
            format="json",
        )
        self.assertEquals(404, resp.status_code)

    def test_patch_correct_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "w", field_name="barcode")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {"barcode": "xxxxx"},
            format="json",
        )
        self.assertEqual(200, resp.status_code, resp.content)
        data = resp.json()
        self.assertDictContainsSubset(
            {
                "message": "The object has been updated but you have no permission to view it.",
                "code": "success_hidden",
            },
            data,
        )
        self.pr1.refresh_from_db()
        self.assertEquals(self.pr1.barcode, "xxxxx")

    def test_patch_correct_permissions_readable(self) -> None:
        p.add_perms_shortcut(self.user, Product, "w", field_name="barcode")
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {"barcode": "xxxxx"},
            format="json",
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {
                "id": str(self.pr1.id),
                "barcode": "xxxxx",
                "brand_id": str(self.br1.id),
            },
            data,
        )
        self.pr1.refresh_from_db()
        self.assertEquals(self.pr1.barcode, "xxxxx")

    def test_patch_fk_no_permissions(self) -> None:
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {
                "brand_id": str(self.br2.id),
            },
            format="json",
        )
        self.assertEquals(404, resp.status_code)

    def test_patch_fk_no_permissions_except_product_w(self) -> None:
        p.add_perms_shortcut(self.user, Product, "w", field_name="brand")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {
                "brand_id": str(self.br2.id),
            },
            format="json",
        )
        self.assertEquals(404, resp.status_code)

    def test_patch_fk_incorrect_perms(self) -> None:
        p.add_perms_shortcut(self.user, Product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, Brand, "rcd")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            data={
                "brand_id": str(self.br2.id),
            },
            format="json",
        )
        self.assertEquals(403, resp.status_code, resp.content)

    def test_patch_fk_correct_perms(self) -> None:
        p.add_perms_shortcut(self.user, Product, "w", field_name="brand")
        p.add_perms_shortcut(self.user, Brand, "rwcd")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            data={
                "brand_id": str(self.br2.id),
            },
            format="json",
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {
                "message": "The object has been updated but you have no permission to view it.",
                "code": "success_hidden",
            },
            data,
        )
        self.pr1.refresh_from_db()
        self.assertEquals(self.pr1.brand, self.br2)

    def test_patch_fk_correct_perms_v2(self) -> None:
        p.add_perms_shortcut(self.user, self.pr1, "w", field_name="brand")
        p.add_perms_shortcut(self.user, self.pr1, "r")
        p.add_perms_shortcut(self.user, Brand, "w")
        resp = self.user_client.patch(
            f"/product/{self.pr1.id}",
            {
                "brand_id": str(self.br2.id),
            },
            format="json",
        )
        self.pr1.refresh_from_db()
        self.assertEqual(self.pr1.brand, self.br2)
        self.assertDictContainsSubset(
            {
                "id": str(self.pr1.id),
                "barcode": "pr1",
                "brand_id": str(self.br2.id),
            },
            resp.json(),
        )
