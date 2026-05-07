import csv
from collections import defaultdict


def parse_cookie_log(filepath):
    """
    Parses a cookie log CSV into (cookie, date) tuples.
    Expects a header row (cookie,timestamp) followed by data rows.
    Raises ValueError on malformed rows, FileNotFoundError if path is invalid.
    """
    entries = []
    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for lineno, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) < 2:
                raise ValueError(f"Malformed row at line {lineno}: {row}")
            cookie, timestamp = row[0], row[1]
            entries.append((cookie, timestamp.split("T")[0]))
    return entries


def find_most_active_cookies(target_date, entries):
    """
    entries: iterable of (cookie, date_str) tuples, date_str as "YYYY-MM-DD"
    Returns list of cookies with the highest occurrence count on target_date.
    """
    counts = defaultdict(int)
    for cookie, date in entries:
        if date == target_date:
            counts[cookie] += 1
    if not counts:
        return []
    max_count = max(counts.values())
    return [cookie for cookie, count in counts.items() if count == max_count]
