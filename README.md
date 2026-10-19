# victorhub-event-log

The event log used by VictorHub, standalone: append JSON Lines events, query them
by type or actor, aggregate counts and rotate the file when it grows.

## Features

- `emit`, `query`, `stats`, `rotate` API and CLI.
- UTC timestamps, monotonically appended, never rewritten.
- Rotation keeps a bounded number of archived files.
- Streams the file line by line for large logs.
- Tests cover append, filters, stats and rotation.

## Installation

```bash
git clone https://github.com/victor-harden/victorhub-event-log.git
cd victorhub-event-log
```

## Usage

```bash
python3 eventlog.py --path events.jsonl emit login victor
python3 eventlog.py --path events.jsonl query --type login
python3 eventlog.py --path events.jsonl stats
python3 eventlog.py --path events.jsonl rotate --keep 3
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
