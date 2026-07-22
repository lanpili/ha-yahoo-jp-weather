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
        self.assertIn(f"## {manifest['version']}", (ROOT / "CHANGELOG.md").read_text())
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

        def keys(value: object, prefix: str = "") -> set[str]:
            if not isinstance(value, dict):
                return {prefix}
            return {
                item
                for key, child in value.items()
                for item in keys(child, f"{prefix}.{key}" if prefix else key)
            }

        reference_keys = keys(strings)
        for path in (COMPONENT / "translations").glob("*.json"):
            data = json.loads(path.read_text())
            self.assertEqual(keys(data), reference_keys)

    def test_github_actions_are_pinned_to_commit_shas(self) -> None:
        for path in (ROOT / ".github" / "workflows").glob("*.yml"):
            for line in path.read_text().splitlines():
                if "uses:" not in line:
                    continue
                reference = line.split("uses:", 1)[1].strip().split()[0]
                if reference.startswith("./"):
                    continue
                with self.subTest(path=path.name, reference=reference):
                    self.assertRegex(reference, r"^[^@]+@[0-9a-f]{40}$")

    def test_hacs_release_archive_metadata(self) -> None:
        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertTrue(hacs["zip_release"])
        self.assertEqual(hacs["filename"], "yahoo_jp_weather.zip")

    def test_release_requires_full_validation_and_main_ancestry(self) -> None:
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text()
        self.assertIn("uses: ./.github/workflows/validate.yml", release)
        self.assertIn("needs: validate", release)
        self.assertIn('git merge-base --is-ancestor "$GITHUB_SHA" origin/main', release)


if __name__ == "__main__":
    unittest.main()
