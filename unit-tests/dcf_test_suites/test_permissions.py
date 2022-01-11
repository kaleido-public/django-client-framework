from dcf_test_app.models import Product
from django.test import TestCase

from django_client_framework import permissions as p
from django_client_framework.models import get_user_model


class TestPermissions(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create()
        self.product = Product.objects.create()

    def test_assign(self) -> None:
        self.assertFalse(p.has_perms_shortcut(self.user, self.product, "r"))
        p.add_perms_shortcut(self.user, self.product, "r")
        self.assertTrue(p.has_perms_shortcut(self.user, self.product, "r"))

    def test_assign_field(self) -> None:
        self.assertFalse(p.has_perms_shortcut(self.user, self.product, "r", "brand"))
        p.add_perms_shortcut(self.user, self.product, "r")
        self.assertTrue(p.has_perms_shortcut(self.user, self.product, "r", "brand"))
