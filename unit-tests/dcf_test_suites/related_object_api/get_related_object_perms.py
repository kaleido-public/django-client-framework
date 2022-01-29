from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_dcf_user_model

User = get_dcf_user_model()


class TestGetPerms(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)
        p.clear_permissions()

    def test_get_no_permissions(self) -> None:
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_incorrect_parent_permission(self) -> None:
        p.add_perms_shortcut(self.user, Product, "wcd", field_name="brand")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_correct(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_correct_ver_2(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r", field_name="brand")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r", field_name="brand")
        p.add_perms_shortcut(self.user, Brand, "wcd")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm_ver_2(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r")
        p.add_perms_shortcut(self.user, Brand, "wcd", field_name="name")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm_ver_3(self) -> None:
        p.add_perms_shortcut(self.user, self.pr1, "r")
        p.add_perms_shortcut(self.user, self.br2, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_incorrect_reverse_perm_ver_4(self) -> None:
        p.add_perms_shortcut(self.user, self.pr1, "r")
        p.add_perms_shortcut(self.user, self.br1, "r", field_name="name")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEquals(404, resp.status_code)

    def test_get_only_parent_permission_correct_reverse_perm(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r", field_name="brand")
        p.add_perms_shortcut(self.user, Brand, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        data = resp.json()
        self.assertDictContainsSubset({"id": str(self.br1.id), "name": "br1"}, data)

    def test_get_only_parent_permission_correct_reverse_perm_ver_2(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r")
        p.add_perms_shortcut(self.user, Brand, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        self.assertEqual(200, resp.status_code, resp.content)
        data = resp.json()
        self.assertDictContainsSubset({"id": str(self.br1.id), "name": "br1"}, data)

    def test_get_only_parent_permission_correct_reverse_perm_ver_3(self) -> None:
        p.add_perms_shortcut(self.user, self.pr1, "r", field_name="brand")
        p.add_perms_shortcut(self.user, self.br1, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        data = resp.json()
        self.assertDictContainsSubset({"id": str(self.br1.id), "name": "br1"}, data)

    def test_get_only_parent_permission_correct_reverse_perm_ver_4(self) -> None:
        p.add_perms_shortcut(self.user, self.pr1, "r")
        p.add_perms_shortcut(self.user, self.br1, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}/brand")
        data = resp.json()
        self.assertDictContainsSubset({"id": str(self.br1.id), "name": "br1"}, data)
