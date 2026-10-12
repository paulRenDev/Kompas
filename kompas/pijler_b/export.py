"""Decoding the sheet export robustly.

The Drive tool returns the sheet as base64 text that the Routine has to
copy into a file by hand -- its result can't be piped to disk. Long copies
pick up stray spaces and, worse, lose their tail (12/10/2026: "the base64
could only be copied into a file by hand and came out corrupted (stray
spaces, watchlist truncated)"; the same on 5/10). One bad copy in three
meant Paul's portfolio silently went stale.

The positions block sits near the top of the export and the watchlist at the
bottom, so a lost tail almost always costs only watchlist rows. This module
cleans what is harmless (whitespace, stray characters), cuts a ragged end to
the last complete base64 group, and says whether it did -- so the cycle can
still publish reconciled positions while leaving the watchlist untouched.
Reconciliation stays the real gate: if the tail loss reached a position,
the totals won't match the sheet's summary row and nothing is published.

CLI:  python3 -m kompas.pijler_b.export sheet.b64 sheet.csv
"""

from __future__ import annotations

import base64
import re
import sys
from dataclasses import dataclass

_NOT_B64 = re.compile(r"[^A-Za-z0-9+/=]")


@dataclass(frozen=True)
class DecodedExport:
    text: str
    truncated: bool  # the copy lost its tail (or was damaged): don't trust the watchlist


def decode_export(b64_text: str) -> DecodedExport:
    cleaned = _NOT_B64.sub("", b64_text)
    body = cleaned.rstrip("=")
    padding = len(cleaned) - len(body)
    truncated = False
    if (len(body) + padding) % 4:
        # ragged end: keep only complete 4-character groups
        body = body[: len(body) // 4 * 4]
        padding = 0
        truncated = True
    raw = base64.b64decode(body + "=" * padding)
    text = raw.decode("utf-8", errors="replace")
    if "�" in text:
        truncated = True
    return DecodedExport(text=text, truncated=truncated)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python3 -m kompas.pijler_b.export <in.b64> <out.csv>")
        return 2
    with open(argv[1], encoding="ascii", errors="ignore") as f:
        result = decode_export(f.read())
    with open(argv[2], "w", encoding="utf-8") as f:
        f.write(result.text)
    print(f"truncated: {'yes' if result.truncated else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
