from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_dcf_user_model
from django_client_framework.permissions import reset_permissions

User = get_dcf_user_model()


class TestGetPerms(TestCase):
    def setUp(self) -> None:
        reset_permissions()
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

    def test_get_without_permissions(self) -> None:
        resp = self.user_client.get(f"/product/{self.pr1.id}")
        self.assertEquals(404, resp.status_code)

    def test_get_incorrect_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "wcd")
        resp = self.user_client.get(f"/product/{self.pr1.id}")
        self.assertEquals(404, resp.status_code)

    def test_get_incorrect_permissions_ver_2(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r", field_name="barcode")
        resp = self.user_client.get(f"/product/{self.pr1.id}")
        self.assertEquals(404, resp.status_code)

    def test_get_correct_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get(f"/product/{self.pr1.id}")
        self.assertDictContainsSubset(
            {"id": str(self.pr1.id), "barcode": "pr1", "brand_id": str(self.br1.id)},
            resp.json(),
        )
