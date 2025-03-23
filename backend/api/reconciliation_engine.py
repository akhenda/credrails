import csv
import datetime
import io

from django.template import loader

# Temporary in-memory database
# Key = report_id (string/UUID), Value = reconciliation results (dict, etc.)
REPORTS = {}


def parse_csv(file_obj):
    """
    Read CSV from an uploaded file and return a list of dictionaries.
    Each dictionary is one row of the CSV with headers as keys.
    """
    data = file_obj.read().decode('utf-8', errors='ignore')
    # We use StringIO to treat the string data as a file-like object
    csv_data = csv.DictReader(io.StringIO(data))

    return list(csv_data)


def normalize_record(record):
    """
    Perform any normalization needed (trimming, lower-casing, date-formatting, etc.)
    and return the cleaned record.
    """
    normalized = {}
    for k, v in record.items():
        if v is None:
            normalized[k] = None
            continue

        # Trim spaces
        v_clean = v.strip()

        # Let us attempt to parse the date or any other data format we want to parse
        try:
            parsed_date = datetime.datetime.strptime(v_clean, '%Y-%m-%d')
            # reformat to a standard ISO date
            v_clean = parsed_date.strftime('%a, %-d %B, %Y')
        except ValueError:
            # If not a date, just do case normalization.
            v_clean = v_clean.lower()

        normalized[k] = v_clean

    return normalized


def build_key(record):
    """
    Here, we define how we identify unique rows. For instance, if the CSV has an
    'id' field, we use that as a unique key. Otherwise, we might combine multiple
    fields. For this assessment task, we assume there's a unique 'id' column.
    """
    return record.get('id')


def reconcile_data(source_data, target_data):
    """
    Given two lists of normalized dictionaries, return:
    - records_missing_in_target
    - records_missing_in_source
    - discrepancies: a list of (key, differences_dict) where differences_dict
      shows which fields differ
    """
    # Build dictionaries keyed by some unique ID or combination
    source_dict = {build_key(r): r for r in source_data}
    target_dict = {build_key(r): r for r in target_data}

    source_keys = set(source_dict.keys())
    target_keys = set(target_dict.keys())

    # Missing in target => in source but not in target
    missing_in_target = []
    for key in source_keys.difference(target_keys):
        missing_in_target.append(source_dict[key])

    # Missing in source => in target but not in source
    missing_in_source = []
    for key in target_keys.difference(source_keys):
        missing_in_source.append(target_dict[key])

    # Discrepancies => records that exist in both but differ in at least one field
    discrepancies = []
    intersection_keys = source_keys.intersection(target_keys)
    fields = set()
    for key in intersection_keys:
        s_record = source_dict[key]
        t_record = target_dict[key]

        # Compare field by field
        record_diffs = {}
        all_fields = set(s_record.keys()).union(set(t_record.keys()))
        for field in all_fields:
            fields.add(field)
            s_val = s_record.get(field)
            t_val = t_record.get(field)
            if s_val != t_val:
                record_diffs[field] = {'source': s_val, 'target': t_val}

        if record_diffs:
            discrepancies.append({'id': key, 'differences': record_diffs})

    if len(REPORTS) > 0:
        report_id = str(max(int(key) for key in REPORTS.keys()) + 1)
    else:
        report_id = '1'

    REPORTS[report_id] = {
        'fields': fields,
        'missing_in_target': missing_in_target,
        'missing_in_source': missing_in_source,
        'discrepancies': discrepancies,
        'created_at': datetime.datetime.now(),
    }

    return report_id, fields, missing_in_target, missing_in_source, discrepancies


def generate_csv(results):
    """
    Turn the results dictionary into a CSV file in-memory and return it.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Section', 'Record'])

    for record in results['missing_in_target']:
        writer.writerow(['missing_in_target', record])
    for record in results['missing_in_source']:
        writer.writerow(['missing_in_source', record])
    for discrepancy in results['discrepancies']:
        writer.writerow(['discrepancy', discrepancy])

    return output


def generate_html(results):
    """
    Convert the results into minimal HTML.
    """
    template = loader.get_template('reconciliation-rich.html')
    html = template.render(results)

    return html
