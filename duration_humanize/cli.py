"""Convert between seconds and human-readable durations.

Parses '1h30m', '90m', '2 days 3h', ISO 8601 'PT1H30M'; formats seconds as
compact ('1h30m'), long ('1 hour 30 minutes') or ISO 8601 durations.

Exit codes:
    0 - success
    1 - I/O or CLI usage error
    2 - at least one input could not be parsed
"""

import argparse
import json
import re
import sys

UNITS = {
    "ns": 1e-9, "us": 1e-6, "ms": 1e-3,
    "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
    "d": 86400, "day": 86400, "days": 86400,
    "w": 604800, "week": 604800, "weeks": 604800,
}

PART_RE = re.compile(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)")
ISO_RE = re.compile(
    r"^P(?:(\d+(?:\.\d+)?)D)?(?:T(?:(\d+(?:\.\d+)?)H)?"
    r"(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?)?$", re.I)


def parse(text):
    text = text.strip()
    if not text:
        raise ValueError("empty duration")
    m = ISO_RE.match(text)
    if m and any(m.groups()):
        d, h, mi, s = (float(g) if g else 0.0 for g in m.groups())
        return d * 86400 + h * 3600 + mi * 60 + s
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
        total += float(m.group(1)) * UNITS[unit]
        pos = m.end()
    if text[pos:].strip() or pos == 0:
        raise ValueError(f"unparseable duration: {text!r}")
    return total


def fmt_compact(sec):
    sign = "-" if sec < 0 else ""
    sec = abs(sec)
    if sec < 1:
        return f"{sec:g}s"
    parts = []
    for unit, size in (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60)):
        q, sec = divmod(int(sec), size)
        if q:
            parts.append(f"{q}{unit}")
    if sec:
        parts.append(f"{sec}s")
    return sign + ("".join(parts) or "0s")


def fmt_long(sec):
    sign = "-" if sec < 0 else ""
    sec = abs(int(sec))
    parts = []
    for name, size in (("week", 604800), ("day", 86400), ("hour", 3600),
                       ("minute", 60), ("second", 1)):
        q, sec = divmod(sec, size)
        if q:
            parts.append(f"{q} {name}" + ("s" if q > 1 else ""))
    return sign + (" ".join(parts) or "0 seconds")


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
        description="Convert seconds <-> human durations (compact/long/ISO 8601).",
    )
    p.add_argument("values", nargs="*", help="durations or seconds; '-' = stdin")
    p.add_argument("-f", "--format", choices=["compact", "long", "iso", "seconds"],
                   default="compact", help="output format (default: compact)")
    p.add_argument("--json", action="store_true", help="emit results as JSON")
    args = p.parse_args(argv)

    values = args.values or ["-"]
    items = []
    for v in values:
        if v == "-":
            items.extend(l for l in sys.stdin.read().splitlines() if l.strip())
        else:
            items.append(v)

    results, errors = [], []
    for item in items:
        try:
            sec = parse(item)
        except ValueError as exc:
            errors.append({"input": item, "error": str(exc)})
            continue
        rendered = {
            "compact": fmt_compact, "long": fmt_long,
            "iso": fmt_iso, "seconds": lambda s: f"{s:g}",
        }[args.format](sec)
        results.append({"input": item, "seconds": sec, "output": rendered})

    if args.json:
        print(json.dumps({"results": results, "errors": errors}, indent=2))
    else:
        for r in results:
            print(f"{r['input']} -> {r['output']}")
        for e in errors:
            print(f"duration-humanize: {e['input']}: {e['error']}", file=sys.stderr)
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
