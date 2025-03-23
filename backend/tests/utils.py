import csv
import io


def make_csv_file(rows):
    """
    Returns an in-memory CSV file (BytesIO) for testing.
    `rows` should be a list of dictionaries, each representing a row.
    """
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    output.seek(0)
    return io.BytesIO(output.getvalue().encode('utf-8'))
