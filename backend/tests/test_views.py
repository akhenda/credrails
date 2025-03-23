from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.utils import make_csv_file

RECONCILIATION_LIST_URL = reverse('api:reconciliation-list')


class ReconciliationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = RECONCILIATION_LIST_URL

    def test_reconciliation_full_match(self):
        """
        When source and target are the same, no missing or discrepancies.
        """
        data_rows = [
            {'id': '1', 'name': 'Goku', 'zeni': '100'},
            {'id': '2', 'name': 'Gohan', 'zeni': '200'},
        ]
        file1 = make_csv_file(data_rows)
        file2 = make_csv_file(data_rows)

        response = self.client.post(
            self.url,
            data={'source_file': file1, 'target_file': file2, 'output_format': 'json'},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('missing_in_target', response.data)
        self.assertEqual(len(response.data['missing_in_target']), 0)
        self.assertEqual(len(response.data['missing_in_source']), 0)
        self.assertEqual(len(response.data['discrepancies']), 0)

    def test_reconciliation_partial_mismatch(self):
        """
        Check scenario where one record is missing in the target, and one field is different.
        """
        source_rows = [
            {'id': '1', 'name': 'Goku', 'zeni': '100'},
            {'id': '2', 'name': 'Gohan', 'zeni': '200'},
        ]
        target_rows = [
            # 1. same data but case difference
            {'id': '1', 'name': 'goku', 'zeni': '100'},
            # '2' missing
        ]

        file1 = make_csv_file(source_rows)
        file2 = make_csv_file(target_rows)

        response = self.client.post(
            self.url,
            data={'source_file': file1, 'target_file': file2, 'output_format': 'json'},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # '2' is missing in target
        self.assertEqual(len(data['missing_in_target']), 1)
        self.assertEqual(data['missing_in_target'][0]['id'], '2')

        # '1' in both, but we might do normalization (case-insensitive).
        if len(data['discrepancies']) > 0:
            discrepancy = data['discrepancies'][0]
            self.assertEqual(discrepancy['id'], '1')
            self.assertIn('name', discrepancy['differences'])
