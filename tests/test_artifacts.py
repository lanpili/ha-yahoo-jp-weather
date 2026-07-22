from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "yahoo_jp_weather"


class IntegrationArtifactTests(unittest.TestCase):
    def test_manifest_and_three_locales_are_present(self) -> None:
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], "yahoo_jp_weather")
        self.assertTrue(manifest["version"])
        self.assertTrue(manifest["config_flow"])
        for filename in ("config_flow.py", "coordinator.py", "weather.py"):
            self.assertTrue((COMPONENT / filename).is_file(), filename)

        expected = {
            "en": "Yahoo! Japan Weather",
            "ja": "Yahoo!天気",
            "zh-Hans": "Yahoo!日本天气",
        }
        for locale, name in expected.items():
            with self.subTest(locale=locale):
                data = json.loads(
                    (COMPONENT / "translations" / f"{locale}.json").read_text()
                )
                self.assertEqual(data["entity"]["weather"]["forecast"]["name"], name)

    def test_translation_keys_match_strings(self) -> None:
        strings = json.loads((COMPONENT / "strings.json").read_text())
        reference_keys = set(strings["entity"]["weather"]["forecast"])
        for path in (COMPONENT / "translations").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertEqual(
                set(data["entity"]["weather"]["forecast"]), reference_keys
            )


if __name__ == "__main__":
    unittest.main()
