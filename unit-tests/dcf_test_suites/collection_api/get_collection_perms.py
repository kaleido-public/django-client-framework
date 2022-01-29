from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_dcf_user_model
from django_client_framework.permissions import default_groups

User = get_dcf_user_model()


class GetPerms(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

        p.clear_permissions()

    def test_get_without_permissions(self) -> None:
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({"objects_count": 0, "objects": []}, data)
        self.assertEqual(resp.status_code, 200)

    def test_incorrect_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "wcd")
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset({"objects_count": 0, "objects": []}, data)
        self.assertEqual(resp.status_code, 200)

    def test_get_all_with_model_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.get("/product")
        data = resp.json()

        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 2}, data
        )
        objects = data["objects"]
        self.assertEqual(len(objects), 2)

    def test_get_r_on_object(self) -> None:
        p.add_perms_shortcut(self.user, self.pr2, "r")
        resp = self.user_client.get("/product")
        data = resp.json()
        self.assertDictContainsSubset(
            {"page": 1, "limit": 50, "objects_count": 1}, data
        )
        objects = data["objects"]
        self.assertDictContainsSubset(
            {"barcode": "pr2", "brand_id": str(self.br2.id), "id": str(self.pr2.id)},
            objects[0],
        )


class TestAnonymous(TestCase):
    def setUp(self) -> None:
        self.user_client = APIClient()

    def test_get_anonymous(self) -> None:
        p.set_perms_shortcut(default_groups.anyone, Product, "r")
        Product.objects.create()
        resp = self.user_client.get("/product")
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, resp.json()["objects_count"])
