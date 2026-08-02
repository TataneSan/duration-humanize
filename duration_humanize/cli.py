"""Convert between seconds and human-readable durations.

Parses '1h30m', '90m', '2 days 3h', ISO 8601 'PT1H30M', plain seconds and
French short forms ('2j 3h'); formats seconds as compact ('1h30m'), long
('1 hour 30 minutes'), ISO 8601 ('PT1H30M') or raw seconds.

Exit codes:
    0 - success
    1 - I/O or CLI usage error
    2 - unparseable input or --require-range gate not satisfied
"""

import argparse
import json
import re
import sys

UNITS = {
    "ns": 1e-9, "us": 1e-6, "µs": 1e-6, "ms": 1e-3,
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "heure": 3600, "heures": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "j": 86400, "jour": 86400, "jours": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
    "sem": 604800, "semaine": 604800, "semaines": 604800,
}

PART_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*([a-zA-Zµ]+)")
ISO_RE = re.compile(
    r"^P(?:(\d+(?:\.\d+)?)W)?(?:(\d+(?:\.\d+)?)D)?(?:T(?:(\d+(?:\.\d+)?)H)?"
    r"(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?)?$", re.I)

LONG_NAMES = {
    "en": (("week", 604800), ("day", 86400), ("hour", 3600),
           ("minute", 60), ("second", 1)),
    "fr": (("semaine", 604800), ("jour", 86400), ("heure", 3600),
           ("minute", 60), ("seconde", 1)),
}


def parse(text):
    """Parse a duration string into seconds (float). Raises ValueError."""
    text = text.strip()
    if not text:
        raise ValueError("empty duration")
    m = ISO_RE.match(text)
    if m and any(m.groups()):
        w, d, h, mi, s = (float(g) if g else 0.0 for g in m.groups())
        return w * 604800 + d * 86400 + h * 3600 + mi * 60 + s
    try:
        return float(text)
    except ValueError:
        pass
    total, pos = 0.0, 0
    for m in PART_RE.finditer(text):
        between = text[pos:m.start()].strip()
        if between:
            raise ValueError(f"unparseable segment: {between!r}")
        unit = m.group(2).lower()
        if unit not in UNITS:
            raise ValueError(f"unknown unit: {m.group(2)!r}")
        total += float(m.group(1).replace(",", ".")) * UNITS[unit]
        pos = m.end()
    if text[pos:].strip() or pos == 0:
        raise ValueError(f"unparseable duration: {text!r}")
    return total


def fmt_compact(sec, locale="en"):
    sign = "-" if sec < 0 else ""
    sec = abs(sec)
    d_unit = "j" if locale == "fr" else "d"
    if sec < 1:
        return f"{sec:g}s"
    parts = []
    for unit, size in ((("sem" if locale == "fr" else "w"), 604800),
                       (d_unit, 86400), ("h", 3600), ("m", 60)):
        q, sec = divmod(int(sec), size)
        if q:
            parts.append(f"{q}{unit}")
    if sec:
        parts.append(f"{sec}s")
    return sign + ("".join(parts) or "0s")


def fmt_long(sec, locale="en"):
    sign = "-" if sec < 0 else ""
    sec = abs(int(sec))
    parts = []
    for name, size in LONG_NAMES.get(locale, LONG_NAMES["en"]):
        q, sec = divmod(sec, size)
        if q:
            parts.append(f"{q} {name}" + ("s" if q > 1 else ""))
    zero = "0 secondes" if locale == "fr" else "0 seconds"
    return sign + (" ".join(parts) or zero)


def fmt_iso(sec):
    sign = "-" if sec < 0 else ""
    sec = abs(int(sec))
    d, sec = divmod(sec, 86400)
    h, sec = divmod(sec, 3600)
    m, s = divmod(sec, 60)
    out = "P"
    if d:
        out += f"{d}D"
    if h or m or s or out == "P":
        out += "T"
        if h:
            out += f"{h}H"
        if m:
            out += f"{m}M"
        if s or out.endswith("T"):
            out += f"{s}S"
    return sign + out


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="duration-humanize",
        description="Convert seconds <-> human durations "
                    "(compact/long/ISO 8601).",
    )
    p.add_argument("values", nargs="*", help="durations or seconds; '-' = stdin")
    p.add_argument("-f", "--format", choices=["compact", "long", "iso", "seconds"],
                   default="compact", help="output format (default: compact)")
    p.add_argument("--round", dest="round_unit",
                   choices=["ms", "s", "m", "h", "d"],
                   help="round parsed seconds to the nearest unit before output")
    p.add_argument("--locale", choices=["en", "fr"], default="en",
                   help="language of long/compact unit words (default: en)")
    p.add_argument("--require-range", nargs=2, metavar=("MIN", "MAX"),
                   type=float,
                   help="exit 2 if any parsed value is outside [MIN, MAX] seconds")
    p.add_argument("--json", action="store_true", help="emit results as JSON")
    args = p.parse_args(argv)

    values = args.values or ["-"]
    items = []
    for v in values:
        if v == "-":
            items.extend(l for l in sys.stdin.read().splitlines() if l.strip())
        else:
            items.append(v)

    rounders = {"ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}

    results, errors, gate_failures = [], [], []
    for item in items:
        try:
            sec = parse(item)
        except ValueError as exc:
            errors.append({"input": item, "error": str(exc)})
            continue
        if args.round_unit:
            step = rounders[args.round_unit]
            sec = round(sec / step) * step
            if args.round_unit == "ms":
                sec = round(sec, 3)
        if args.require_range:
            lo, hi = args.require_range
            if not (lo <= sec <= hi):
                gate_failures.append(item)
        rendered = {
            "compact": lambda s: fmt_compact(s, args.locale),
            "long": lambda s: fmt_long(s, args.locale),
            "iso": fmt_iso,
            "seconds": lambda s: f"{s:g}",
        }[args.format](sec)
        results.append({"input": item, "seconds": sec, "output": rendered})

    if args.json:
        print(json.dumps({
            "results": results,
            "errors": errors,
            "gate_failures": gate_failures,
        }, indent=2, ensure_ascii=False))
    else:
        for r in results:
            print(f"{r['input']} -> {r['output']}")
        for e in errors:
            print(f"duration-humanize: {e['input']}: {e['error']}",
                  file=sys.stderr)
        for g in gate_failures:
            lo, hi = args.require_range
            print(f"duration-humanize: {g}: outside required range "
                  f"[{lo}, {hi}] seconds", file=sys.stderr)
    return 2 if (errors or gate_failures) else 0


if __name__ == "__main__":
    sys.exit(main())
