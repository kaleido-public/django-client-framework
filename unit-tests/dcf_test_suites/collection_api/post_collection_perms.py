from dcf_test_app.models import Brand, Product
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p


class PostPerms(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.br1 = Brand.objects.create(name="br1")
        self.br2 = Brand.objects.create(name="br2")
        self.pr1 = Product.objects.create(barcode="pr1", brand=self.br1)
        self.pr2 = Product.objects.create(barcode="pr2", brand=self.br2)

        p.clear_permissions()

    def test_post_without_permissions(self) -> None:
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        self.assertEqual(403, resp.status_code)

    def test_post_only_read_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "r")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        self.assertEqual(403, resp.status_code)

    def test_post_only_create_permissions(self) -> None:
        """You can create by can't see"""
        p.add_perms_shortcut(self.user, Product, "c")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        data = resp.json()
        self.assertDictContainsSubset(
            {
                "general_errors": [
                    "The object has been created but you have no permission to view it."
                ],
            },
            data,
        )

    def test_post_read_create_permissions(self) -> None:
        p.add_perms_shortcut(self.user, Product, "rc")
        resp = self.user_client.post("/product", {"barcode": "pr3"})
        data = resp.json()
        self.assertDictContainsSubset({"barcode": "pr3", "brand_id": None}, data)

    def test_post_with_object_permissions(self) -> None:
        """Test rc on object perm instead of model. Creation should be denied."""
        p.add_perms_shortcut(self.user, Product.objects.all(), "rc")
        resp = self.user_client.post("/product", {"asdf": "pr3"})
        self.assertEqual(403, resp.status_code)

    def test_post_foreignkey(self) -> None:
        p.add_perms_shortcut(self.user, Product, "rc")
        p.add_perms_shortcut(self.user, Brand, "w")
        resp = self.user_client.post(
            "/product", {"barcode": "pr3", "brand_id": str(self.br1.id)}
        )
        data = resp.json()
        self.assertDictContainsSubset(
            {"barcode": "pr3", "brand_id": str(self.br1.id)}, data
        )

    def test_post_with_fk_without_read(self) -> None:
        """Post FK without read permission. The API should hide the existence of
        the FK object by responding 404."""
        p.add_perms_shortcut(self.user, Product, "c")
        resp = self.user_client.post(
            "/product", {"barcode": "pr3", "brand_id": str(self.br1.id)}
        )
        self.assertEquals(resp.status_code, 404)

    def test_post_with_fk_incorrect_perm(self) -> None:
        """"""
        p.add_perms_shortcut(self.user, Product, "c")
        p.add_perms_shortcut(self.user, Brand, "rcd")
        resp = self.user_client.post(
            "/product", {"barcode": "pr3", "brand_id": str(self.br1.id)}
        )
        self.assertEquals(resp.status_code, 403)
