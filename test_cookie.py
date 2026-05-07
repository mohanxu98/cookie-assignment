import os
import subprocess
import tempfile

import pytest

from cookie_finder import find_most_active_cookies, parse_cookie_log

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(PROJECT_DIR, "most_active_cookie")

# Pre-parsed entries matching cookie_log.csv (header excluded, timestamps reduced to dates)
SAMPLE_ENTRIES = [
    ("AtY0laUfhglK3lC7", "2018-12-09"),
    ("SAZuXPGUrfbcn5UA", "2018-12-09"),
    ("5UAVanZf6UtGyKVS", "2018-12-09"),
    ("AtY0laUfhglK3lC7", "2018-12-09"),
    ("SAZuXPGUrfbcn5UA", "2018-12-08"),
    ("4sMM2LxV07bPJzwf", "2018-12-08"),
    ("fbcn5UAVanZf6UtG", "2018-12-08"),
    ("4sMM2LxV07bPJzwf", "2018-12-07"),
]


# Testing Basic Functionality: expected behavior on typical inputs

class TestBasicFunctionality:
    """Behavior testing using well-formed (cookie, date_str) tuples."""

    def test_single_winner(self):
        result = find_most_active_cookies("2018-12-09", SAMPLE_ENTRIES)
        assert result == ["AtY0laUfhglK3lC7"], (
            f"Expected ['AtY0laUfhglK3lC7'] — AtY0laUfhglK3lC7 appears twice on "
            f"2018-12-09, all others once. Got: {result}"
        )

    def test_three_way_tie(self):
        result = find_most_active_cookies("2018-12-08", SAMPLE_ENTRIES)
        expected = sorted(["SAZuXPGUrfbcn5UA", "4sMM2LxV07bPJzwf", "fbcn5UAVanZf6UtG"])
        assert sorted(result) == expected, (
            f"Expected all 3 cookies tied at 1 occurrence each on 2018-12-08. Got: {result}"
        )

    def test_single_occurrence_on_date(self):
        result = find_most_active_cookies("2018-12-07", SAMPLE_ENTRIES)
        assert result == ["4sMM2LxV07bPJzwf"], (
            f"Expected ['4sMM2LxV07bPJzwf'] — only cookie on 2018-12-07. Got: {result}"
        )

    def test_only_counts_matching_date(self):
        result = find_most_active_cookies("2018-12-09", SAMPLE_ENTRIES)
        assert result == ["AtY0laUfhglK3lC7"], (
            f"Cross-date counts leaking: SAZuXPGUrfbcn5UA appears 3x total but only "
            f"1x on 2018-12-09 and should not dominate. Got: {result}"
        )

    def test_two_way_tie(self):
        entries = [("AAA", "2018-12-09"), ("BBB", "2018-12-09")]
        result = find_most_active_cookies("2018-12-09", entries)
        assert sorted(result) == ["AAA", "BBB"], (
            f"Expected both AAA and BBB with equal count of 1. Got: {result}"
        )

    def test_no_matches_returns_empty_list(self):
        result = find_most_active_cookies("2099-01-01", SAMPLE_ENTRIES)
        assert result == [], (
            f"Expected [] for a date with no entries. Got: {result}"
        )

    def test_empty_input_returns_empty_list(self):
        result = find_most_active_cookies("2018-12-09", [])
        assert result == [], (
            f"Expected [] for empty input. Got: {result}"
        )

    def test_single_entry_returns_that_cookie(self):
        result = find_most_active_cookies("2018-12-09", [("OnlyCookie", "2018-12-09")])
        assert result == ["OnlyCookie"], (
            f"Expected ['OnlyCookie'] as the sole entry on the date. Got: {result}"
        )


# Testing Edge Cases: valid inputs that are unusual / at boundaries of expected input space

class TestEdgeCases:
    """Boundary and unusual-but-valid inputs."""

    def test_same_cookie_repeated(self):
        entries = [("AAA", "2018-12-09")] * 3
        result = find_most_active_cookies("2018-12-09", entries)
        assert result == ["AAA"], (
            f"Expected ['AAA'] when the same cookie appears 3 times. Got: {result}"
        )

    def test_many_cookies_all_tied(self):
        entries = [(f"COOKIE{i}", "2018-12-09") for i in range(10)]
        result = find_most_active_cookies("2018-12-09", entries)
        expected = sorted([f"COOKIE{i}" for i in range(10)])
        assert sorted(result) == expected, (
            f"Expected all 10 cookies returned when each appears exactly once. Got: {result}"
        )

    def test_wrong_date_format_returns_empty(self):
        result = find_most_active_cookies("09-12-2018", SAMPLE_ENTRIES)
        assert result == [], (
            f"'09-12-2018' is DD-MM-YYYY format and should never match YYYY-MM-DD "
            f"date strings. Got: {result}"
        )

    def test_partial_date_string_returns_empty(self):
        result = find_most_active_cookies("2018-12", SAMPLE_ENTRIES)
        assert result == [], (
            f"Partial date '2018-12' should not match full date strings. Got: {result}"
        )

    def test_generator_input(self):
        result = find_most_active_cookies("2018-12-09", iter(SAMPLE_ENTRIES))
        assert result == ["AtY0laUfhglK3lC7"], (
            f"Function must accept any iterable, not just lists. Got: {result}"
        )


# Testing CSV Parsing: file I/O, csv module correctness, error handling in parse_cookie_log

class TestCSVParsing:
    """Tests for parse_cookie_log: file I/O, csv module correctness, error handling."""

    def _make_csv(self, lines):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, dir=PROJECT_DIR
        )
        f.write("\n".join(lines))
        f.close()
        return f.name

    def test_parses_standard_file(self):
        path = self._make_csv([
            "cookie,timestamp",
            "AtY0laUfhglK3lC7,2018-12-09T14:19:00+00:00",
            "SAZuXPGUrfbcn5UA,2018-12-08T10:13:00+00:00",
        ])
        try:
            result = parse_cookie_log(path)
            expected = [("AtY0laUfhglK3lC7", "2018-12-09"), ("SAZuXPGUrfbcn5UA", "2018-12-08")]
            assert result == expected, (
                f"Expected {expected}. Got: {result}"
            )
        finally:
            os.unlink(path)

    def test_strips_date_from_iso_timestamp(self):
        path = self._make_csv([
            "cookie,timestamp",
            "ABC,2018-12-09T14:19:00+00:00",
        ])
        try:
            result = parse_cookie_log(path)
            assert result == [("ABC", "2018-12-09")], (
                f"Timestamp '2018-12-09T14:19:00+00:00' should reduce to date '2018-12-09'. Got: {result}"
            )
        finally:
            os.unlink(path)

    def test_skips_empty_lines(self):
        path = self._make_csv([
            "cookie,timestamp",
            "ABC,2018-12-09T14:19:00+00:00",
            "",
            "DEF,2018-12-09T10:00:00+00:00",
        ])
        try:
            result = parse_cookie_log(path)
            expected = [("ABC", "2018-12-09"), ("DEF", "2018-12-09")]
            assert result == expected, (
                f"Empty lines should be skipped, not cause errors. Got: {result}"
            )
        finally:
            os.unlink(path)

    def test_header_only_returns_empty_list(self):
        path = self._make_csv(["cookie,timestamp"])
        try:
            result = parse_cookie_log(path)
            assert result == [], (
                f"A file with only a header row should return []. Got: {result}"
            )
        finally:
            os.unlink(path)

    def test_quoted_fields_with_commas_handled(self):
        path = self._make_csv([
            "cookie,timestamp",
            '"cookie,withcomma",2018-12-09T14:19:00+00:00',
        ])
        try:
            result = parse_cookie_log(path)
            assert result == [("cookie,withcomma", "2018-12-09")], (
                f"csv.reader should handle quoted fields with commas inside. Got: {result}"
            )
        finally:
            os.unlink(path)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError, match="nonexistent_file.csv"):
            parse_cookie_log("nonexistent_file.csv")

    def test_malformed_row_too_few_columns_raises(self):
        path = self._make_csv(["cookie,timestamp", "MALFORMEDROW"])
        try:
            with pytest.raises(ValueError, match="Malformed row at line 2"):
                parse_cookie_log(path)
        finally:
            os.unlink(path)

    def test_sample_file_parses_all_rows(self):
        result = parse_cookie_log(os.path.join(PROJECT_DIR, "cookie_log.csv"))
        assert len(result) == 8, (
            f"cookie_log.csv has 8 data rows (excluding header). Got {len(result)} rows."
        )
        assert result[0] == ("AtY0laUfhglK3lC7", "2018-12-09"), (
            f"First row should be ('AtY0laUfhglK3lC7', '2018-12-09'). Got: {result[0]}"
        )
        assert result[-1] == ("4sMM2LxV07bPJzwf", "2018-12-07"), (
            f"Last row should be ('4sMM2LxV07bPJzwf', '2018-12-07'). Got: {result[-1]}"
        )


# Testing CLI Integration: end-to-end test from command line, generate CSV files, check stdout and stderr, check exit codes

class TestCLIIntegration:
    """End-to-end tests through the most_active_cookie entry point."""

    def _make_csv(self, data_rows):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, dir=PROJECT_DIR
        )
        f.write("cookie,timestamp\n")
        for row in data_rows:
            f.write(row + "\n")
        f.close()
        return f.name

    def _run(self, *args):
        return subprocess.run(
            [CLI, *args],
            capture_output=True, text=True, cwd=PROJECT_DIR,
        )

    def test_single_winner(self):
        path = self._make_csv([
            "AtY0laUfhglK3lC7,2018-12-09T14:19:00+00:00",
            "SAZuXPGUrfbcn5UA,2018-12-09T10:13:00+00:00",
            "AtY0laUfhglK3lC7,2018-12-09T06:19:00+00:00",
        ])
        try:
            result = self._run(path, "-d", "2018-12-09")
            assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"
            assert result.stdout.strip() == "AtY0laUfhglK3lC7", (
                f"Expected 'AtY0laUfhglK3lC7' as sole winner. Got: '{result.stdout.strip()}'"
            )
        finally:
            os.unlink(path)

    def test_tied_winners_all_printed(self):
        path = self._make_csv([
            "AAA,2018-12-09T10:00:00+00:00",
            "BBB,2018-12-09T09:00:00+00:00",
        ])
        try:
            result = self._run(path, "-d", "2018-12-09")
            assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"
            assert sorted(result.stdout.strip().splitlines()) == ["AAA", "BBB"], (
                f"All tied cookies must be printed, one per line. Got: '{result.stdout.strip()}'"
            )
        finally:
            os.unlink(path)

    def test_no_match_prints_nothing(self):
        path = self._make_csv(["AtY0laUfhglK3lC7,2018-12-09T14:19:00+00:00"])
        try:
            result = self._run(path, "-d", "2099-01-01")
            assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"
            assert result.stdout.strip() == "", (
                f"Expected empty output when no cookies match the date. Got: '{result.stdout.strip()}'"
            )
        finally:
            os.unlink(path)

    def test_file_not_found_exits_nonzero(self):
        result = self._run("nonexistent_file.csv", "-d", "2018-12-09")
        assert result.returncode == 1, (
            f"Expected exit code 1 for missing file. Got: {result.returncode}"
        )
        assert "not found" in result.stderr.lower(), (
            f"Expected 'not found' in stderr. Got: '{result.stderr}'"
        )

    def test_missing_date_flag_exits_nonzero(self):
        result = self._run("cookie_log.csv")
        assert result.returncode != 0, (
            f"Expected non-zero exit code when -d flag is missing. Got: {result.returncode}"
        )

    def test_sample_file_dec9(self):
        result = self._run("cookie_log.csv", "-d", "2018-12-09")
        assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"
        assert result.stdout.strip() == "AtY0laUfhglK3lC7", (
            f"Expected 'AtY0laUfhglK3lC7' for 2018-12-09 in sample file. Got: '{result.stdout.strip()}'"
        )

    def test_sample_file_dec8(self):
        result = self._run("cookie_log.csv", "-d", "2018-12-08")
        assert result.returncode == 0, f"Expected exit code 0. stderr: {result.stderr}"
        expected = sorted(["SAZuXPGUrfbcn5UA", "4sMM2LxV07bPJzwf", "fbcn5UAVanZf6UtG"])
        actual = sorted(result.stdout.strip().splitlines())
        assert actual == expected, (
            f"Expected 3-way tie on 2018-12-08: {expected}. Got: {actual}"
        )
