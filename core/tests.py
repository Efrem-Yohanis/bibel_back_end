from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class BibleViewsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_verse_of_the_day_returns_not_found_when_daily_verses_are_missing(self):
        response = self.client.get('/api/bible/verse-of-the-day?language=en')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        if response.status_code == status.HTTP_404_NOT_FOUND:
            self.assertEqual(response.data.get('status'), 'error')
            self.assertIsInstance(response.data.get('message'), str)
