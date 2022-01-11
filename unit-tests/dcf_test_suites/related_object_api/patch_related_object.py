from uuid import UUID

from dcf_test_app.models import Brand, Product
from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.models import get_user_model


class TestRetrieve(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.superuser = User.objects.create(username="testuser", is_superuser=True)
        self.superuser_client = APIClient()
        self.superuser_client.force_authenticate(self.superuser)
        self.brands = [Brand.objects.create(name=f"brand_{i+1}") for i in range(5)]
        self.product = Product.objects.create()

    def test_patch_success(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.product.id}/brand",
            data=str(self.brands[0].id),
            format="json",
        )
        self.assertEqual(200, resp.status_code, resp.content)
        self.product.refresh_from_db()
        self.assertEqual(self.brands[0], self.product.brand, resp.json())

    def test_patch_failed_invalid_fk(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.product.id}/brand",
            data=UUID(int=23),
            format="json",
        )
        self.assertEqual(404, resp.status_code, resp.content)
        data = resp.json()
        self.assertDictContainsSubset(
            {"general_errors": [f"Not Found: Brand ({UUID(int=23)})"]},
            data,
            data,
        )

    def test_patch_array(self) -> None:
        resp = self.superuser_client.patch(
            f"/product/{self.product.id}/brand",
            data=[UUID(int=23), UUID(int=24)],
            format="json",
        )
        self.assertEqual(400, resp.status_code, resp.content)
        data = resp.json()
        self.assertEqual(
            data["general_errors"],
            [
                f"Expected an object pk in the request body, but received list: ['{UUID(int=23)}', '{UUID(int=24)}']"
            ],
        )
