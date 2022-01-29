from dcf_test_app.models import Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_dcf_user_model
from django_client_framework.permissions import default_users, reset_permissions

User = get_dcf_user_model()


class TestDeleteObject(TestCase):
    def setUp(self) -> None:
        reset_permissions()
        self.user = default_users.root
        self.user_client = APIClient()
        self.user_client.force_authenticate(self.user)
        self.pr1 = Product.objects.create()

    def test_delete_success(self) -> None:
        assert Product.objects.count() == 1
        resp = self.user_client.delete(f"/product/{self.pr1.id}")
        self.assertEqual(204, resp.status_code, resp.content)
        self.assertEqual(0, Product.objects.count())
