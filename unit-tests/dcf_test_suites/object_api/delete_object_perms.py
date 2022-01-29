from dcf_test_app.models import Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework import permissions as p
from django_client_framework.models import get_dcf_user_model

User = get_dcf_user_model()


class TestDeleteObject(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(username="testuser")
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.pr1 = Product.objects.create()

    def test_delete_perm(self) -> None:
        p.set_perms_shortcut(self.user, self.pr1, "d")
        assert Product.objects.count() == 1
        resp = self.user_client.delete(f"/product/{self.pr1.id}")
        self.assertEqual(204, resp.status_code, resp.content)
        self.assertEqual(0, Product.objects.count())

    def test_no_delete_perm(self) -> None:
        assert Product.objects.count() == 1
        resp = self.user_client.delete(f"/product/{self.pr1.id}")
        self.assertEqual(404, resp.status_code, resp.content)
        self.assertEqual(1, Product.objects.count())
