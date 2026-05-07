# cookie-assignment
Take Home Assessment 

## File Structure

```
cookie-assignment/
├── most_active_cookie      # CLI entry point
├── cookie_finder.py        # Core logic: parse_cookie_log, find_most_active_cookies
├── test_cookie.py          # Test suite (pytest)
├── cookie_log.csv          # Sample input file
└── requirements.txt        # Dependencies
```

### `cookie_finder.py`
- **`parse_cookie_log(filepath)`** — reads a CSV file, skips the header row, returns a list of `(cookie, date_str)` tuples where `date_str` is `YYYY-MM-DD`
- **`find_most_active_cookies(target_date, entries)`** — takes an iterable of `(cookie, date_str)` tuples and a target date string, returns a list of all cookies tied for the highest count on that date (empty list if no matches)

### `most_active_cookie`
CLI entry point. Parses arguments, calls `parse_cookie_log` and `find_most_active_cookies` core logic functions, prints one cookie per line to stdout.

**Usage:**
```
./most_active_cookie <path_to_csv> -d <YYYY-MM-DD>
```

**Input:** CSV file with a `cookie,timestamp` header followed by rows of `<cookie_id>,<ISO8601 timestamp>`

**Output:** One cookie ID per line (all cookies tied for most active on the given date). Empty output if no cookies found for that date.

**Exit codes:** `0` on success, `1` if the file is not found

**Example:**
```
$ ./most_active_cookie cookie_log.csv -d 2018-12-09
AtY0laUfhglK3lC7
```



## Testing architecture 
Located in test_cookie.py, designed to for testing most_active_cookie in three layers:
1. Basic logic handling: tests function logic for most active cookies (calls find most_active_cookies within most_active_cookie.py) with well formatted, pre-set inputs

2. tests boundary conditions on find_most_active_cookies — all cookies tied, one cookie dominating all rows, unrecognized date formats, partial date strings, and generator inputs to verify the function accepts any iterable

3. CSV parsing handling: tests the parse_cookie_log function in isolation including file I/O errors, correct date extraction from ISO timestamps, empty line skipping, malformed row detection with line numbers, and quoted field handling via the csv module. Kept separate from logic tests so parsing failures and counting failures are never conflated


## Design Choices / Implementation Notes

1. Core cookie aggregation logic is separated from CLI handling to improve testability and maintainability
2. Used `defaultdict(int)` for efficient frequency counting
3. Date filtering is performed during file iteration to avoid unnecessary intermediate storage
4. Error handling was added for invalid file paths and malformed input rows

## Scalability For Future
1. Consider using generator function to parse inputs instead of loading CSV all at once if input file is very large 
2. 