# Contributing

Thank you for helping improve Yahoo! Japan Weather for Home Assistant.

## Development setup

1. Install Python 3.14.
2. Create a virtual environment.
3. Install `requirements-test.txt`.
4. Make focused changes with regression tests.

```bash
python -m pip install --requirement requirements-test.txt
pytest -q --cov=custom_components.yahoo_jp_weather --cov-report=term-missing
ruff check custom_components tests scripts
ruff format --check custom_components tests scripts
mypy custom_components/yahoo_jp_weather
```

## Pull requests

- Keep location and account data out of fixtures and logs.
- Use synthetic HTML fixtures where possible.
- Parser changes must include a regression test for the exact Yahoo markup variation.
- Config-entry changes must preserve entity unique IDs unless a migration is provided.
- Do not reduce coverage below the configured threshold.
- Update translations and documentation for user-visible changes.

## Live page probe

`scripts/live_probe.py` contacts a fixed Yahoo municipality page. It is intentionally excluded from normal pull-request tests and runs weekly to detect upstream markup changes without sending a request on every commit.
