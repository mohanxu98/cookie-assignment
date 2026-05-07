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


# Testing Basic Funciionlity: expected behavior on typical inputs 

class TestBasicFunctionality:
    """Behavior testing using well-formed (cookie, date_str) tuples."""

    def test_single_winner(self):
        # AtY0laUfhglK3lC7 appears twice on 2018-12-09, all others once
        assert find_most_active_cookies("2018-12-09", SAMPLE_ENTRIES) == ["AtY0laUfhglK3lC7"]

    def test_three_way_tie(self):
        result = find_most_active_cookies("2018-12-08", SAMPLE_ENTRIES)
        #sorted to avoid order dependence since all three have same count of 1 on 2018-12-08
        assert sorted(result) == sorted(["SAZuXPGUrfbcn5UA", "4sMM2LxV07bPJzwf", "fbcn5UAVanZf6UtG"])

    def test_single_occurrence_on_date(self):
        assert find_most_active_cookies("2018-12-07", SAMPLE_ENTRIES) == ["4sMM2LxV07bPJzwf"]

    def test_only_counts_matching_date(self):
        #SAZuXPGUrfbcn5UA appears 3x total but only 1x on 2018-12-09 — should not dominate
        assert find_most_active_cookies("2018-12-09", SAMPLE_ENTRIES) == ["AtY0laUfhglK3lC7"]

    def test_two_way_tie(self):
        entries = [("AAA", "2018-12-09"), ("BBB", "2018-12-09")]
        assert sorted(find_most_active_cookies("2018-12-09", entries)) == ["AAA", "BBB"]

    def test_no_matches_returns_empty_list(self):
        assert find_most_active_cookies("2099-01-01", SAMPLE_ENTRIES) == []

    def test_empty_input_returns_empty_list(self):
        assert find_most_active_cookies("2018-12-09", []) == []

    def test_single_entry_returns_that_cookie(self):
        assert find_most_active_cookies("2018-12-09", [("OnlyCookie", "2018-12-09")]) == ["OnlyCookie"]


# Testing Edge Cases: valid inputs that are unusual / at boundaries of expected input space 

class TestEdgeCases:
    """Boundary and unusual-but-valid inputs."""

    def test_same_cookie_repeated(self):
        entries = [("AAA", "2018-12-09")] * 3
        assert find_most_active_cookies("2018-12-09", entries) == ["AAA"]

    def test_many_cookies_all_tied(self):
        entries = [(f"COOKIE{i}", "2018-12-09") for i in range(10)]
        result = find_most_active_cookies("2018-12-09", entries)
        assert sorted(result) == sorted([f"COOKIE{i}" for i in range(10)])

    def test_wrong_date_format_returns_empty(self):
        #"09-12-2018" will never equal "2018-12-09"
        assert find_most_active_cookies("09-12-2018", SAMPLE_ENTRIES) == []

    def test_partial_date_string_returns_empty(self):
        assert find_most_active_cookies("2018-12", SAMPLE_ENTRIES) == []

    def test_generator_input(self):
        # entries can be any iterable, not just a list
        assert find_most_active_cookies("2018-12-09", iter(SAMPLE_ENTRIES)) == ["AtY0laUfhglK3lC7"]


#Testing CSV Parsing: file I/O, csv module correctness, error handling in parse_cookie_log

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
            assert parse_cookie_log(path) == [
                ("AtY0laUfhglK3lC7", "2018-12-09"),
                ("SAZuXPGUrfbcn5UA", "2018-12-08"),
            ]
        finally:
            os.unlink(path)

    def test_strips_date_from_iso_timestamp(self):
        path = self._make_csv([
            "cookie,timestamp",
            "ABC,2018-12-09T14:19:00+00:00",
        ])
        try:
            assert parse_cookie_log(path) == [("ABC", "2018-12-09")]
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
            assert parse_cookie_log(path) == [
                ("ABC", "2018-12-09"),
                ("DEF", "2018-12-09"),
            ]
        finally:
            os.unlink(path)

    def test_header_only_returns_empty_list(self):
        path = self._make_csv(["cookie,timestamp"])
        try:
            assert parse_cookie_log(path) == []
        finally:
            os.unlink(path)

    def test_quoted_fields_with_commas_handled(self):
        # csv module correctly handles quoted fields containing commas
        path = self._make_csv([
            "cookie,timestamp",
            '"cookie,withcomma",2018-12-09T14:19:00+00:00',
        ])
        try:
            assert parse_cookie_log(path) == [("cookie,withcomma", "2018-12-09")]
        finally:
            os.unlink(path)

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
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
        assert len(result) == 8
        assert result[0] == ("AtY0laUfhglK3lC7", "2018-12-09")
        assert result[-1] == ("4sMM2LxV07bPJzwf", "2018-12-07")


#Testing CLI Integration: end-to-end test from command line, generate CSV files, check stdout and stderr, check exit codes 

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
            ["python3", CLI, *args],
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
            assert result.returncode == 0
            assert result.stdout.strip() == "AtY0laUfhglK3lC7"
        finally:
            os.unlink(path)

    def test_tied_winners_all_printed(self):
        path = self._make_csv([
            "AAA,2018-12-09T10:00:00+00:00",
            "BBB,2018-12-09T09:00:00+00:00",
        ])
        try:
            result = self._run(path, "-d", "2018-12-09")
            assert result.returncode == 0
            assert sorted(result.stdout.strip().splitlines()) == ["AAA", "BBB"]
        finally:
            os.unlink(path)

    def test_no_match_prints_nothing(self):
        path = self._make_csv(["AtY0laUfhglK3lC7,2018-12-09T14:19:00+00:00"])
        try:
            result = self._run(path, "-d", "2099-01-01")
            assert result.returncode == 0
            assert result.stdout.strip() == ""
        finally:
            os.unlink(path)

    def test_file_not_found_exits_nonzero(self):
        result = self._run("nonexistent_file.csv", "-d", "2018-12-09")
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_missing_date_flag_exits_nonzero(self):
        result = self._run("cookie_log.csv")
        assert result.returncode != 0

    def test_sample_file_dec9(self):
        result = self._run("cookie_log.csv", "-d", "2018-12-09")
        assert result.returncode == 0
        assert result.stdout.strip() == "AtY0laUfhglK3lC7"

    def test_sample_file_dec8(self):
        result = self._run("cookie_log.csv", "-d", "2018-12-08")
        assert result.returncode == 0
        assert sorted(result.stdout.strip().splitlines()) == sorted(
            ["SAZuXPGUrfbcn5UA", "4sMM2LxV07bPJzwf", "fbcn5UAVanZf6UtG"]
        )
