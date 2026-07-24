import json
from pathlib import Path

import pytest

from scripts.validate_dashboard_i18n import LanguagePackError, validate_directory

LANGUAGE_PACKS = Path(__file__).parents[1] / "dashboard/yahoo-weather-card-i18n"


def test_repository_language_packs_are_valid() -> None:
    assert validate_directory(LANGUAGE_PACKS) == ["en", "ja", "zh"]


def test_new_language_requires_only_an_additional_json_file(tmp_path: Path) -> None:
    pack = json.loads((LANGUAGE_PACKS / "en.json").read_text(encoding="utf-8"))
    pack["locale"] = "fr-FR"
    pack["hourly"] = "Heure par heure"
    pack["daily"] = "Prévisions quotidiennes"
    pack["tabAliases"] = {
        "hourly": ["Heure par heure"],
        "daily": ["Prévisions quotidiennes"],
    }
    (tmp_path / "fr.json").write_text(
        json.dumps(pack, ensure_ascii=False), encoding="utf-8"
    )

    assert validate_directory(tmp_path) == ["fr"]


def test_missing_translation_key_is_rejected(tmp_path: Path) -> None:
    pack = json.loads((LANGUAGE_PACKS / "en.json").read_text(encoding="utf-8"))
    del pack["sunset"]
    (tmp_path / "en.json").write_text(json.dumps(pack), encoding="utf-8")

    with pytest.raises(LanguagePackError, match="sunset"):
        validate_directory(tmp_path)
