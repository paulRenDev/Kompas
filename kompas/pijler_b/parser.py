"""Google Sheet adapter — vertaallaag.

Pure functions: sheet text in, kompas.core.schema objects out. No I/O here
— fetching and writing are separate, thin layers. Keeping this file pure is
what makes it testable without a live session.

Two input formats, one set of parsing rules: the old pipe-table dump from
mcp__Google_Drive__read_file_content (parse_aandelen_dump), and the CSV
export of the "live" tab via mcp__Google_Drive__download_file_content with
exportMimeType="text/csv" (parse_aandelen_csv). The CSV path exists because
read_file_content changed format in September 2026 and now returns only a
sampled summary of each tab — no complete PORTEFEUILLE rows — which silently
froze the portfolio data at 18/9. Both paths reduce to rows of cells first,
so the header-matching rules below apply identically to either.

Two real bugs were made against this exact data before this file existed
(see README, "Werkelijke portefeuille-structuur"), and both are encoded
here as the rule that caused them, not just fixed in the output:

1. Never assume which row is "the totals row" by position. The dump
   contains more than one plausible-looking totals row; the real one is
   identified by its own header line, always.
2. Never assume column meaning carries across two blocks shaped alike.
   PORTEFEUILLE's `purchaseDate`/`totPurValueEUR` and Watchlist's
   `setDate`/`totSetValueEUR` are NOT the same thing wearing a different
   header — they are parsed into different dataclasses (Position vs.
   WatchlistEntry) on purpose, so a caller can never accidentally treat a
   watch candidate's opportunity-cost gain as real P&L.
"""

from __future__ import annotations

import csv
import io
import re

from kompas.core.schema import (
    PortfolioSnapshot,
    PortfolioSummary,
    Position,
    WatchlistEntry,
)

PORTFOLIO_SUMMARY_HEADER = ["valueEUR", "aankValueEUR", "Rendement", "Rendement%"]
PORTFOLIO_TABLE_HEADER_PREFIX = ["Name", "TICKER", "EXCHANGE", "Type effect", "currency", "purchaseDate (min)"]
WATCHLIST_TABLE_HEADER_PREFIX = ["Name", "TICKER", "EXCHANGE", "Type effect", "currency", "OPM", "setDate (min)"]


class ParseError(ValueError):
    """Raised when an expected header/row cannot be found — never guess."""


def _split_row(line: str) -> list[str]:
    """A pipe-table row -> stripped cells, dropping the leading/trailing empty cell."""
    cells = line.split("|")
    if len(cells) >= 2 and cells[0].strip() == "" and cells[-1].strip() == "":
        cells = cells[1:-1]
    return [c.strip() for c in cells]


def _is_blank_row(cells: list[str]) -> bool:
    return all(c == "" for c in cells)


def parse_number(raw: str) -> float | None:
    """European-format amount/percentage -> float. '' -> None.

    Handles: '€ 420,13', '\\-€ 55,47', '1,99%', '\\-0,14', '5.846,0'.
    """
    if raw is None:
        return None
    s = raw.strip()
    if s == "":
        return None
    negative = False
    if s.startswith("\\-"):
        negative = True
        s = s[2:]
    elif s.startswith("-"):
        negative = True
        s = s[1:]
    s = s.replace("€", "").replace("\\&", "&").replace("%", "").strip()
    s = s.replace(".", "").replace(",", ".")
    if s == "" or s == "-":
        return None
    try:
        value = float(s)
    except ValueError:
        return None
    return -value if negative else value


def _find_row(rows: list[list[str]], predicate) -> int:
    for i, cells in enumerate(rows):
        if predicate(cells):
            return i
    return -1


def _optional_col_index(header_cells: list[str], name: str) -> int | None:
    try:
        return _col_index(header_cells, name)
    except ParseError:
        return None


def _cell(cells: list[str], i: int | None) -> str:
    return cells[i] if i is not None and i < len(cells) else ""


def _col_index(header_cells: list[str], name: str) -> int:
    for i, cell in enumerate(header_cells):
        if cell.strip() == name:
            return i
    raise ParseError(f"column {name!r} not found in header {header_cells!r}")


def parse_portfolio_summary(rows: list[list[str]]) -> PortfolioSummary:
    header_idx = _find_row(
        rows,
        lambda cells: cells[:4] == PORTFOLIO_SUMMARY_HEADER,
    )
    if header_idx == -1:
        raise ParseError("portfolio summary header row not found — sheet layout may have changed")
    data_cells = rows[header_idx + 1]
    value = parse_number(data_cells[0])
    cost = parse_number(data_cells[1])
    gain = parse_number(data_cells[2])
    gain_pct = parse_number(data_cells[3])
    if None in (value, cost, gain, gain_pct):
        raise ParseError(f"portfolio summary row had an unparseable cell: {data_cells[:4]!r}")
    # The unlabelled fifth cell is the day's change in EUR ("-€ 34,17").
    day_change = parse_number(_cell(data_cells, 4))
    return PortfolioSummary(
        value_eur=value, cost_eur=cost, gain_eur=gain, gain_pct=gain_pct, day_change_eur=day_change
    )


def parse_positions(rows: list[list[str]]) -> list[Position]:
    header_idx = _find_row(
        rows,
        lambda cells: cells[: len(PORTFOLIO_TABLE_HEADER_PREFIX)] == PORTFOLIO_TABLE_HEADER_PREFIX,
    )
    if header_idx == -1:
        raise ParseError("PORTEFEUILLE table header not found")
    header = rows[header_idx]
    i_name = _col_index(header, "Name")
    i_ticker = _col_index(header, "TICKER")
    i_exchange = _col_index(header, "EXCHANGE")
    i_type = _col_index(header, "Type effect")
    i_currency = _col_index(header, "currency")
    i_qty = _col_index(header, "Nbr")
    i_cost = _col_index(header, "totPurValueEUR")
    i_value = _col_index(header, "valueEUR")
    i_gain = _col_index(header, "Rendement(EUR)")
    i_gain_pct = _col_index(header, "Rendement(EUR%)")
    i_day = _optional_col_index(header, "Change(vsYday%)")

    positions: list[Position] = []
    for cells in rows[header_idx + 1 :]:
        if _is_blank_row(cells) or len(cells) <= i_gain_pct:
            break
        name = cells[i_name]
        if name == "":
            break
        positions.append(
            Position(
                name=name.replace("\\&", "&"),
                ticker=cells[i_ticker],
                exchange=cells[i_exchange],
                type_effect=cells[i_type],
                currency=cells[i_currency],
                qty=parse_number(cells[i_qty]) or 0.0,
                cost_eur=parse_number(cells[i_cost]) or 0.0,
                value_eur=parse_number(cells[i_value]) or 0.0,
                gain_eur=parse_number(cells[i_gain]) or 0.0,
                gain_pct=parse_number(cells[i_gain_pct]) or 0.0,
                day_change_pct=parse_number(_cell(cells, i_day)),
            )
        )
    return positions


def parse_watchlist(rows: list[list[str]]) -> list[WatchlistEntry]:
    header_idx = _find_row(
        rows,
        lambda cells: cells[: len(WATCHLIST_TABLE_HEADER_PREFIX)] == WATCHLIST_TABLE_HEADER_PREFIX,
    )
    if header_idx == -1:
        raise ParseError("Watchlist table header not found")
    header = rows[header_idx]
    i_name = _col_index(header, "Name")
    i_ticker = _col_index(header, "TICKER")
    i_exchange = _col_index(header, "EXCHANGE")
    i_type = _col_index(header, "Type effect")
    i_currency = _col_index(header, "currency")
    i_set_date = _col_index(header, "setDate (min)")
    i_ref_value = _col_index(header, "totSetValueEUR")
    i_cur_value = _col_index(header, "valueEUR")
    i_gain = _col_index(header, "Rendement(EUR)")
    i_gain_pct = _col_index(header, "Rendement(EUR%)")

    entries: list[WatchlistEntry] = []
    for cells in rows[header_idx + 1 :]:
        if _is_blank_row(cells) or len(cells) <= i_gain_pct:
            break
        name = cells[i_name]
        if name == "":
            break
        entries.append(
            WatchlistEntry(
                name=name.replace("\\&", "&"),
                ticker=cells[i_ticker],
                exchange=cells[i_exchange],
                type_effect=cells[i_type],
                currency=cells[i_currency],
                set_date=cells[i_set_date],
                reference_value_eur=parse_number(cells[i_ref_value]) or 0.0,
                current_value_eur=parse_number(cells[i_cur_value]) or 0.0,
                opportunity_gain_eur=parse_number(cells[i_gain]) or 0.0,
                opportunity_gain_pct=parse_number(cells[i_gain_pct]) or 0.0,
            )
        )
    return entries


def _snapshot_from_rows(rows: list[list[str]]) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        positions=parse_positions(rows),
        watchlist=parse_watchlist(rows),
        summary=parse_portfolio_summary(rows),
    )


def parse_aandelen_dump(raw_text: str) -> PortfolioSnapshot:
    return _snapshot_from_rows([_split_row(line) for line in raw_text.splitlines()])


def parse_aandelen_csv(csv_text: str) -> PortfolioSnapshot:
    rows = [[c.strip() for c in row] for row in csv.reader(io.StringIO(csv_text))]
    return _snapshot_from_rows(rows)
