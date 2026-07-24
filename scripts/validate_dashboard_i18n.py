from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

LANGUAGE_FILE_RE = re.compile(r"^[a-z]{2,3}\.json$")
STRING_KEYS = {
    "locale",
    "defaultTitle",
    "close",
    "forecastType",
    "hourly",
    "daily",
    "loadingHourly",
    "loadingDaily",
    "entityRequired",
    "openDetails",
    "noForecast",
    "loadFailed",
    "dragHint",
    "rain",
    "temperature",
    "probability",
    "precipitation",
    "humidity",
    "windDirection",
    "windSpeed",
    "wind",
    "calm",
    "sunrise",
    "sunset",
    "unknown",
}
REQUIRED_KEYS = STRING_KEYS | {"tabAliases", "conditions", "directions"}


class LanguagePackError(ValueError):
    """Raised when a dashboard language pack is incomplete or malformed."""


def _require_string_mapping(value: Any, location: str) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise LanguagePackError(f"{location} must be a non-empty object")
    if any(
        not isinstance(key, str) or not isinstance(item, str) or not item
        for key, item in value.items()
    ):
        raise LanguagePackError(f"{location} must contain non-empty strings")
    return value


def _validate_pack(path: Path) -> set[str]:
    try:
        pack = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LanguagePackError(f"{path.name}: invalid JSON: {error}") from error
    if not isinstance(pack, dict):
        raise LanguagePackError(f"{path.name}: root must be an object")

    missing = REQUIRED_KEYS - pack.keys()
    extra = pack.keys() - REQUIRED_KEYS
    if missing:
        raise LanguagePackError(
            f"{path.name}: missing keys: {', '.join(sorted(missing))}"
        )
    if extra:
        raise LanguagePackError(
            f"{path.name}: unexpected keys: {', '.join(sorted(extra))}"
        )

    for key in STRING_KEYS:
        if not isinstance(pack[key], str) or not pack[key].strip():
            raise LanguagePackError(f"{path.name}: {key} must be a non-empty string")

    aliases = pack["tabAliases"]
    if not isinstance(aliases, dict) or set(aliases) != {"hourly", "daily"}:
        raise LanguagePackError(f"{path.name}: tabAliases requires hourly and daily")
    for forecast_type in ("hourly", "daily"):
        values = aliases[forecast_type]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
        ):
            raise LanguagePackError(
                f"{path.name}: tabAliases.{forecast_type} requires strings"
            )

    conditions = _require_string_mapping(pack["conditions"], f"{path.name}: conditions")
    directions = pack["directions"]
    if (
        not isinstance(directions, list)
        or len(directions) != 16
        or any(
            not isinstance(direction, str) or not direction for direction in directions
        )
    ):
        raise LanguagePackError(f"{path.name}: directions requires exactly 16 strings")
    return set(conditions)


def validate_directory(directory: Path) -> list[str]:
    """Validate all language packs and return their language codes."""
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise LanguagePackError(f"No language packs found in {directory}")
    expected_conditions: set[str] | None = None
    languages: list[str] = []
    for path in paths:
        if not LANGUAGE_FILE_RE.fullmatch(path.name):
            raise LanguagePackError(
                f"{path.name}: filename must be a lowercase base language code"
            )
        conditions = _validate_pack(path)
        if expected_conditions is None:
            expected_conditions = conditions
        elif conditions != expected_conditions:
            missing = expected_conditions - conditions
            extra = conditions - expected_conditions
            raise LanguagePackError(
                f"{path.name}: condition keys differ; "
                f"missing={sorted(missing)}, extra={sorted(extra)}"
            )
        languages.append(path.stem)
    return languages


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Yahoo weather language packs"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        default=Path(__file__).parents[1] / "dashboard/yahoo-weather-card-i18n",
    )
    args = parser.parse_args()
    languages = validate_directory(args.directory)
    print(f"OK: language packs: {', '.join(languages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
