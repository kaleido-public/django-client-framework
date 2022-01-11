from django.test import TestCase
from rest_framework.test import APIClient

from django_client_framework.api import rate_limit

rate_limit.default = "120/min"


class TestRateLimited(TestCase):
    def test_spam_get(self) -> None:
        client = APIClient()
        for iter in range(20):
            response = client.get(
                "/throttledmodel",
                format="json",
            )
            if iter < 10:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 429)
