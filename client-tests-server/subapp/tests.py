from django.test import TestCase

from .models import Product


class BasicTest(TestCase):
    def test_clear(self):
        Product.objects.create()
        resp = self.client.post("/subapp/clear")
        self.assertContains(resp, "Successfully deleted all.")
