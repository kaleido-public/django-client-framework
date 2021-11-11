from django.test import TestCase
from rest_framework.test import APIClient


class TestRateLimited(TestCase):
    def test_spam_get(self):
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
