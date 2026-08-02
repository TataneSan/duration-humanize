# duration-humanize

Convert between plain seconds and human-readable durations: `1h30m`,
`2 days 3h`, ISO 8601 `PT1H30M`, French short forms (`2j 3h`) — and format
seconds back as compact, long, ISO 8601 or raw values. Pure stdlib, no
dependencies.

## Features

- Parses: `90`, `1h30m`, `2 days 3 hours`, `PT1H30M`, `P1W`, `1.5h`,
  `250ms`, `2jours 3heures`
- Units: `ns`, `us`, `ms`, `s`, `m`, `h`, `d`/`j`, `w` (plus word forms,
  EN and FR)
- Output formats: `compact` (`1h30m`), `long` (`1 hour 30 minutes`),
  `iso` (`PT1H30M`), `seconds`
- `--locale fr` for French unit words (`jour`, `heure`, `semaine`…)
- `--round ms|s|m|h|d` to snap parsed values to a unit
- `--require-range MIN MAX` CI gate: exit 2 when a value falls outside
- Batch mode: positional args, files of values, or stdin (`-`)
- JSON report with `--json`

## Install

```bash
pip install .
# or directly
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

$ duration-humanize -f long --locale fr 90000
90000 -> 1 jour 1 heure

$ printf '1h\n45s\n' | duration-humanize -f seconds -
1h -> 3600
45s -> 45

$ duration-humanize --round m 95
95 -> 2m
```

CI gate example:

```bash
$ duration-humanize --require-range 0 3600 7200
duration-humanize: 7200: outside required range [0.0, 3600.0] seconds
(exit code 2)
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | All inputs parsed and gates satisfied |
| 1 | I/O or CLI error |
| 2 | Unparseable input or `--require-range` violated |

## Tests

```bash
python -m unittest discover -s tests
```

## License

MIT
