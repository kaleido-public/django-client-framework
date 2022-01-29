from dcf_test_app.models import Product
from django.test import TestCase

from django_client_framework.models import UserObjectPermission, get_user_model
from django_client_framework.permissions import (
    add_perms_shortcut,
    filter_queryset_by_perms_shortcut,
    has_perms_shortcut,
)


class TestHasPermission(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create()
        self.product = Product.objects.create()

    def test_assign(self) -> None:
        self.assertFalse(has_perms_shortcut(self.user, self.product, "r"))
        add_perms_shortcut(self.user, self.product, "r")
        self.assertTrue(has_perms_shortcut(self.user, self.product, "r"))

    def test_assign_field(self) -> None:
        self.assertFalse(has_perms_shortcut(self.user, self.product, "r", "brand"))
        add_perms_shortcut(self.user, self.product, "r")
        self.assertTrue(has_perms_shortcut(self.user, self.product, "r", "brand"))

    def test_object_perm_implies_field_perm(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "r")
        self.assertTrue(has_perms_shortcut(self.user, product, "r", "brand"))

    def test_model_perm_implies_object_perm(self) -> None:
        add_perms_shortcut(self.user, Product, "r")
        self.assertTrue(has_perms_shortcut(self.user, self.product, "r"))

    def test_object_perm_implies_field_perm_for_field(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "r", "brand")
        self.assertTrue(has_perms_shortcut(self.user, product, "r", "brand"))

    def test_model_perm_implies_object_perm_for_field(self) -> None:
        add_perms_shortcut(self.user, Product, "r", "brand")
        self.assertTrue(has_perms_shortcut(self.user, self.product, "r", "brand"))

    def test_field_perm_does_not_imply_object_perm(self) -> None:
        add_perms_shortcut(self.user, self.product, "r", field_name="barcode")
        self.assertFalse(has_perms_shortcut(self.user, self.product, "r"))

    def test_object_perm_does_not_imply_model_perm(self) -> None:
        add_perms_shortcut(self.user, self.product, "r")
        self.assertFalse(has_perms_shortcut(self.user, Product, "r"))


class TestAddPermissions(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create()
        self.product = Product.objects.create()

    def test_simple_object_permission(self) -> None:
        add_perms_shortcut(self.user, self.product, "r")
        self.assertEqual(UserObjectPermission.objects.count(), 1)
        uop = UserObjectPermission.objects.get()
        self.assertEqual(uop.user, self.user)
        self.assertEqual(uop.content_object, self.product)

    def test_simple_object_permission_multiple(self) -> None:
        add_perms_shortcut(self.user, self.product, "rwcd")
        self.assertEqual(UserObjectPermission.objects.count(), 4)
        for uop in UserObjectPermission.objects.all():
            self.assertEqual(uop.user, self.user)
            self.assertEqual(uop.content_object, self.product)

    def test_simple_object_permission_multiple_fields(self) -> None:
        add_perms_shortcut(self.user, self.product, "rwcd", field_name="barcode")
        self.assertEqual(UserObjectPermission.objects.count(), 4)
        for uop in UserObjectPermission.objects.all():
            self.assertEqual(uop.user, self.user)
            self.assertEqual(uop.content_object, self.product)
            self.assertEqual(uop.permission.field_name, "barcode")

    def test_add_model_permission(self) -> None:
        add_perms_shortcut(self.user, Product, "rwcd", field_name="barcode")
        self.assertEqual(self.user.model_permissions.count(), 4)
        for perm in self.user.model_permissions.all():
            self.assertEqual(perm.field_name, "barcode")


class TestAddFilterByPermissions(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create()

    def test_filter_simple_object_permission(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "r")
        queryset = filter_queryset_by_perms_shortcut(
            "r", self.user, Product.objects.all()
        )
        self.assertEqual(queryset.count(), 1)

    def test_filter_multiple_objects_permission(self) -> None:
        for _ in range(4):
            product = Product.objects.create()
            add_perms_shortcut(self.user, product, "r")
        for _ in range(6):
            product = Product.objects.create()
        queryset = filter_queryset_by_perms_shortcut(
            "r", self.user, Product.objects.all()
        )
        self.assertEqual(queryset.count(), 4)

    def test_when_multiple_perms_assigned(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "rwc")
        queryset = filter_queryset_by_perms_shortcut(
            "rw", self.user, Product.objects.all()
        )
        self.assertEqual(queryset.count(), 1)

    def test_when_multiple_perms_with_fields_assigned(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "rwc", field_name="barcode")
        queryset = filter_queryset_by_perms_shortcut(
            "rw", self.user, Product.objects.all(), field_name="barcode"
        )
        self.assertEqual(queryset.count(), 1)

    def test_field_perm_does_not_imply_object_perm(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "r", field_name="barcode")
        queryset = filter_queryset_by_perms_shortcut(
            "r", self.user, Product.objects.all()
        )
        self.assertEqual(queryset.count(), 0)

    def test_object_perm_implies_field_perm(self) -> None:
        product = Product.objects.create()
        add_perms_shortcut(self.user, product, "r")
        queryset = filter_queryset_by_perms_shortcut(
            "r", self.user, Product.objects.all(), field_name="barcode"
        )
        self.assertEqual(queryset.count(), 1)

    def test_model_perm_implies_object_perm(self) -> None:
        Product.objects.create()
        add_perms_shortcut(self.user, Product, "rw")
        queryset = filter_queryset_by_perms_shortcut(
            "r", self.user, Product.objects.all()
        )
        self.assertEqual(queryset.count(), 1)
