## Summary

## Verification

- [ ] `pytest -q --cov=custom_components.yahoo_jp_weather --cov-report=term-missing`
- [ ] `ruff check custom_components tests scripts`
- [ ] `ruff format --check custom_components tests scripts`
- [ ] `mypy custom_components/yahoo_jp_weather`
- [ ] User-visible text and translations are updated
- [ ] No private location URLs, addresses, tokens, or unredacted diagnostics are included
- [ ] Entity unique IDs remain stable or a migration is included
