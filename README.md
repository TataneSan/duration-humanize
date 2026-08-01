# duration-humanize

Convert between seconds and human durations: `1h30m`, `2 days 3h`,
ISO 8601 `PT1H30M`, plain seconds — and format back as compact, long or
ISO 8601.

## Features

- Parses: `90`, `1h30m`, `2 days 3 hours`, `PT1H30M`, `1.5h`, `250ms`
- Formats: `compact` (`1h30m`), `long` (`1 hour 30 minutes`),
  `iso` (`PT1H30M`), `seconds`
- Batch mode via stdin
- JSON output, exit 2 on unparseable input
- Pure Python standard library, no dependencies

## Install

```bash
pip install .
pip install git+https://github.com/TataneSan/duration-humanize.git
```

## Usage

```bash
$ duration-humanize 5400 90m '2 days 3h' PT0.25H
5400 -> 1h30m
90m -> 1h30m
2 days 3h -> 2d3h
PT0.25H -> 15m

$ duration-humanize -f iso 3661
3661 -> PT1H1M1S

$ printf '1h\n45s\n' | duration-humanize -f seconds -
1h -> 3600
45s -> 45
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All inputs parsed |
| 1 | I/O or CLI error |
| 2 | Unparseable input |

## License

MIT
