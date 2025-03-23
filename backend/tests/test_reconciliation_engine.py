import io
from unittest.mock import MagicMock, patch

from django.test import TestCase

from api.reconciliation_engine import (
    build_key,
    generate_csv,
    generate_html,
    normalize_record,
    parse_csv,
    reconcile_data,
)
from tests.utils import make_csv_file


class ReconciliationEngineTests(TestCase):
    # -------------------------------------------------------------------------
    # parse_csv
    # -------------------------------------------------------------------------
    def test_parse_csv_returns_list_of_dicts(self):
        """parse_csv should return a list of dictionaries corresponding to CSV rows."""
        rows = [
            {'id': '1', 'name': 'Goku'},
            {'id': '2', 'name': 'Gohan'},
        ]
        csv_file = make_csv_file(rows)
        parsed = parse_csv(csv_file)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['id'], '1')
        self.assertEqual(parsed[0]['name'], 'Goku')
        self.assertEqual(parsed[1]['id'], '2')
        self.assertEqual(parsed[1]['name'], 'Gohan')

    def test_parse_csv_handles_empty_file(self):
        """parse_csv should return an empty list if the file has no content or headers."""
        empty_file = io.BytesIO(b'')
        parsed = parse_csv(empty_file)
        self.assertEqual(parsed, [])

    # -------------------------------------------------------------------------
    # normalize_record
    # -------------------------------------------------------------------------
    def test_normalize_record_trims_and_lowercases(self):
        """normalize_record should trim spaces and convert to lowercase for non-date fields."""
        record = {'id': ' 1 ', 'name': '  GOKU  ', 'info': ' Some Mixed CASE '}
        result = normalize_record(record)

        # 'id' => '1'
        self.assertEqual(result['id'], '1')
        # 'name' => 'goku'
        self.assertEqual(result['name'], 'goku')
        # 'info' => 'some mixed case'
        self.assertEqual(result['info'], 'some mixed case')

    def test_normalize_record_parses_valid_dates(self):
        """normalize_record should parse valid dates (YYYY-MM-DD) and reformat them."""
        record = {
            'id': '1',
            'transaction_date': ' 2025-01-01 ',  # with leading/trailing spaces
        }
        result = normalize_record(record)
        # Date should remain in YYYY-MM-DD format
        self.assertEqual(result['transaction_date'], 'Wed, 1 January, 2025')

    def test_normalize_record_handles_invalid_dates_as_strings(self):
        """
        If date parsing fails, we just treat the value as a string (lower-cased and trimmed).
        """
        record = {'id': '1', 'not_a_date': ' someString '}
        result = normalize_record(record)
        self.assertEqual(result['not_a_date'], 'somestring')

    # -------------------------------------------------------------------------
    # build_key
    # -------------------------------------------------------------------------
    def test_build_key_returns_id_field(self):
        """build_key should return the 'id' field from the record."""
        record = {'id': '123', 'name': 'Goku'}
        self.assertEqual(build_key(record), '123')

    def test_build_key_returns_none_if_no_id(self):
        """If no 'id' is present, build_key returns None."""
        record = {'name': 'Goku'}
        self.assertIsNone(build_key(record))

    # -------------------------------------------------------------------------
    # reconcile_data
    # -------------------------------------------------------------------------
    def test_reconcile_data_no_differences(self):
        """
        If both source_data and target_data are the same,
        there should be no missing records or discrepancies.
        """
        source_data = [
            {'id': '1', 'name': 'goku'},
            {'id': '2', 'name': 'gohan'},
        ]
        target_data = [
            {'id': '1', 'name': 'goku'},
            {'id': '2', 'name': 'gohan'},
        ]
        report_id, fields, missing_in_target, missing_in_source, discrepancies = (
            reconcile_data(source_data, target_data)
        )
        self.assertEqual(fields, {'id', 'name'})
        self.assertEqual(len(missing_in_target), 0)
        self.assertEqual(len(missing_in_source), 0)
        self.assertEqual(len(discrepancies), 0)

    def test_reconcile_data_finds_missing_and_discrepancies(self):
        """
        If one record is missing in the target, and one record has a field mismatch,
        ensure they're reported correctly.
        """
        source_data = [
            {'id': '1', 'name': 'goku', 'tax': '100'},
            {'id': '2', 'name': 'gohan', 'tax': '200'},
        ]
        target_data = [
            {'id': '1', 'name': 'goku', 'tax': '999'},  # mismatch in 'tax'
            # '2' is missing
        ]
        report_id, fields, missing_in_target, missing_in_source, discrepancies = (
            reconcile_data(source_data, target_data)
        )

        # '2' is missing in target
        self.assertEqual(len(missing_in_target), 1)
        self.assertEqual(missing_in_target[0]['id'], '2')

        # There's nothing in the target that's missing in the source
        self.assertEqual(len(missing_in_source), 0)

        # For record '1', we have a discrepancy in 'tax'
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0]['id'], '1')
        self.assertIn('tax', discrepancies[0]['differences'])
        self.assertEqual(discrepancies[0]['differences']['tax']['source'], '100')
        self.assertEqual(discrepancies[0]['differences']['tax']['target'], '999')

    # -------------------------------------------------------------------------
    # generate_csv
    # -------------------------------------------------------------------------
    def test_generate_csv_creates_proper_csv_content(self):
        """
        generate_csv should produce CSV lines that reflect the reconciliation results.
        """
        # Prepare some dummy results
        results = {
            'missing_in_target': [{'id': '2', 'name': 'Gohan'}],
            'missing_in_source': [{'id': '3', 'name': 'Bulma'}],
            'discrepancies': [
                {
                    'id': '1',
                    'differences': {'tax': {'source': '100', 'target': '200'}},
                }
            ],
        }

        # generate_csv is defined with signature generate_csv(self, results),
        # but typically it wouldn't need 'self'. We'll pass None or a dummy for 'self'.
        csv_file = generate_csv(results)
        csv_file.seek(0)
        csv_data = csv_file.read()

        # Now let's check the contents
        csv_rows = csv_data.splitlines()
        # First row: "Section,Record"
        self.assertEqual(csv_rows[0], 'Section,Record')
        # Next rows might be:
        # missing_in_target,"{'id': '2', 'name': 'Gohan'}"
        # missing_in_source,"{'id': '3', 'name': 'Bulma'}"
        # discrepancy,"{'id': '1', 'differences': {'tax': {'source': '100', 'target': '200'}}}"
        self.assertIn("missing_in_target,\"{'id': '2', 'name': 'Gohan'}\"", csv_rows[1])
        self.assertIn("missing_in_source,\"{'id': '3', 'name': 'Bulma'}\"", csv_rows[2])
        self.assertIn(
            "discrepancy,\"{'id': '1', 'differences': {'tax': {'source': '100', 'target': '200'}}}\"",
            csv_rows[3],
        )

    # -------------------------------------------------------------------------
    # generate_html
    # -------------------------------------------------------------------------
    def test_generate_html_renders_template(self):
        """
        generate_html should call Django's template rendering with the correct context.
        """
        results = {
            'missing_in_target': [{'id': '2'}],
            'missing_in_source': [{'id': '3'}],
            'discrepancies': [
                {
                    'id': '1',
                    'differences': {'tax': {'source': '100', 'target': '999'}},
                }
            ],
        }

        mock_template = MagicMock()
        mock_template.render.return_value = '<html>Fake Template Output</html>'

        with patch(
            'django.template.loader.get_template', return_value=mock_template
        ) as mock_get_template:
            html_output = generate_html(results)

            mock_get_template.assert_called_once_with('reconciliation-rich.html')
            mock_template.render.assert_called_once_with(results)

            self.assertEqual(html_output, '<html>Fake Template Output</html>')
