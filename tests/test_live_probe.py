from __future__ import annotations

import unittest
from typing import Any

from scripts import live_probe


class _Response:
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return "https://example.com/redirected"

    def read(self) -> bytes:
        return b"unexpected"


class _Opener:
    def open(self, *args: object, **kwargs: object) -> _Response:
        return _Response()


class LiveProbeTests(unittest.TestCase):
    def test_rejects_changed_final_url(self) -> None:
        fetch_html: Any = getattr(live_probe, "fetch_html", None)
        self.assertIsNotNone(
            fetch_html, "live probe must expose fail-closed fetch_html"
        )

        with self.assertRaisesRegex(RuntimeError, "redirect"):
            fetch_html(opener=_Opener())


if __name__ == "__main__":
    unittest.main()
