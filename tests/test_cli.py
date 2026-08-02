import io
import unittest
from contextlib import redirect_stdout, redirect_stderr

from duration_humanize.cli import main, parse, fmt_compact, fmt_long, fmt_iso


class TestParse(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(parse("90"), 90)

    def test_compact(self):
        self.assertEqual(parse("1h30m"), 5400)

    def test_words(self):
        self.assertEqual(parse("2 days 3 hours"), 183600)

    def test_iso(self):
        self.assertEqual(parse("PT1H30M"), 5400)

    def test_iso_weeks(self):
        self.assertEqual(parse("P1W"), 604800)

    def test_fractional(self):
        self.assertEqual(parse("1.5h"), 5400)

    def test_millis(self):
        self.assertAlmostEqual(parse("250ms"), 0.25)

    def test_french(self):
        self.assertEqual(parse("2j 3h"), 183600)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse("banana")

    def test_trailing_garbage(self):
        with self.assertRaises(ValueError):
            parse("30m x")


class TestFormat(unittest.TestCase):
    def test_compact(self):
        self.assertEqual(fmt_compact(183600), "2d3h")
        self.assertEqual(fmt_compact(183600, "fr"), "2j3h")

    def test_long(self):
        self.assertEqual(fmt_long(5400), "1 hour 30 minutes")
        self.assertEqual(fmt_long(5400, "fr"), "1 heure 30 minutes")

    def test_iso(self):
        self.assertEqual(fmt_iso(90061), "P1DT1H1M1S")
        self.assertEqual(fmt_iso(0), "PT0S")


def run_cli(argv, stdin=""):
    out, err = io.StringIO(), io.StringIO()
    import sys
    old = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
    finally:
        sys.stdin = old
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def test_args(self):
        code, out, _ = run_cli(["5400", "90m"])
        self.assertEqual(code, 0)
        self.assertIn("5400 -> 1h30m", out)
        self.assertIn("90m -> 1h30m", out)

    def test_stdin(self):
        code, out, _ = run_cli(["-f", "seconds", "-"], stdin="1h\n45s\n")
        self.assertEqual(code, 0)
        self.assertIn("1h -> 3600", out)

    def test_long_fr(self):
        code, out, _ = run_cli(["-f", "long", "--locale", "fr", "90000"])
        self.assertEqual(out.strip(), "90000 -> 1 jour 1 heure")

    def test_round(self):
        code, out, _ = run_cli(["--round", "m", "95"])
        self.assertIn("95 -> 2m", out)

    def test_require_range_fail(self):
        code, _, err = run_cli(["--require-range", "0", "100", "200"])
        self.assertEqual(code, 2)
        self.assertIn("outside required range", err)

    def test_require_range_ok(self):
        code, _, _ = run_cli(["--require-range", "0", "100", "50"])
        self.assertEqual(code, 0)

    def test_invalid_exit_2(self):
        code, _, err = run_cli(["nope"])
        self.assertEqual(code, 2)
        self.assertIn("unparseable", err)

    def test_json(self):
        code, out, _ = run_cli(["--json", "1h"])
        self.assertEqual(code, 0)
        self.assertIn('"seconds": 3600', out)


if __name__ == "__main__":
    unittest.main()
