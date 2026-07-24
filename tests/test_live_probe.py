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
        for function_name in ("fetch_html", "fetch_api"):
            fetch: Any = getattr(live_probe, function_name, None)
            self.assertIsNotNone(
                fetch, f"live probe must expose fail-closed {function_name}"
            )

            with (
                self.subTest(function_name=function_name),
                self.assertRaisesRegex(RuntimeError, "redirect"),
            ):
                fetch(opener=_Opener())


if __name__ == "__main__":
    unittest.main()
