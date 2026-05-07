# cookie-assignment
Take Home Assessment 

## File Structure
TO BE ADDED 



## Testing architecture 
Located in test_cookie.py, designed to for testing most_active_cookie in three layers:
1. Basic logic handling: tests function logic for most active cookies (calls find most_active_cookies within most_active_cookie.py) with well formatted, pre-set inputs

2. tests boundary conditions on find_most_active_cookies — all cookies tied, one cookie dominating all rows, unrecognized date formats, partial date strings, and generator inputs to verify the function accepts any iterable

3. CSV parsing handling: tests the parse_cookie_log function in isolation including file I/O errors, correct date extraction from ISO timestamps, empty line skipping, malformed row detection with line numbers, and quoted field handling via the csv module. Kept separate from logic tests so parsing failures and counting failures are never conflated.


## Design Choices / Implementation Notes

- Core cookie aggregation logic is separated from CLI handling to improve testability and maintainability.
- Used `defaultdict(int)` for efficient frequency counting.
- Date filtering is performed during file iteration to avoid unnecessary intermediate storage.
- Error handling was added for invalid file paths and malformed input rows.