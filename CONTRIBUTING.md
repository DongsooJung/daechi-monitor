# Contributing to daechi-monitor

Thanks for taking the time to contribute. This repository runs an automated
monitoring pipeline, so contributions that keep results **reproducible** and
the dashboard **honest** are the most valuable.

## Quick start

```bash
git clone https://github.com/DongsooJung/daechi-monitor.git
cd daechi-monitor
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Contribution flow

1. **Open an issue first** for anything larger than a bug fix.
2. **Branch** from `main`: `git checkout -b <topic>`.
3. **Keep the pipeline reproducible.** Scheduled refreshes must record scan
   times, source queries, and hashes in metadata.
4. **State your assumptions.** Scan scope, dedup rules, and collection
   windows must be stated in code and documentation.
5. **Open a PR** describing what changed and why.

## What the maintainer cares about

- **Honest scope.** If a scan misses a category or a source, say so in the
  dashboard notes.
- **No silent data assumptions.** Reruns must reproduce the same dashboard
  from the same raw inputs.

## Reporting bugs

Open an issue with the exact command, the expected result, and the actual
result. For security concerns, follow `SECURITY.md` instead of the public
issue tracker.

## License

Contributions are accepted under the [MIT License](LICENSE).
