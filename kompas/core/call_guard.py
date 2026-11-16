"""Guards on the morning call -- the lessons from NUCL.

Paul, 16/11/2026: "die uranium [...] was toch een misser hoor. dat gaan we
moeten vermijden". The record shows the team proposed NUCL as four separate
ideas between 28/9 and 13/11, and it went wrong in four ways:
1. 28/9: bought to fill a sleeve. That was a rebalancing reason, banned
   since 30/9.
2. 4/10 and 8/11: "uranium on a record, the shares lag". The gap never
   closed, and the call kept leaning on it.
3. 13-15/11: "39% below the top while uranium holds, so overdone". But NUCL
   also holds reactor builders and small-reactor developers that trade on
   AI sentiment. During an AI sell-off they keep falling, whatever uranium
   does. The team judged the label, not the contents.
4. Farah objected on 9/11, 14/11 and 15/11 with the very risk that then
   played out. On 16/11 her own Fed playbook said "mijd NUCL" until 9/12,
   while the call still said buy.

So, before a buy call goes out, four checks. They live in code so a routine
can't skip them:
- PLAYBOOK CONSISTENCY: no buy in a ticker that a naderend or actief playbook
  says to avoid ("mijd").
- NO FALLING KNIFE: a call whose why-now is a drop needs Mila's floor: no new
  closing low for FLOOR_DAYS trading days, from a sourced chart. Otherwise
  the drop's reason must be resolved by a sourced fact.
- LOOK THROUGH THE FUND: for a fund, say what share of it actually follows
  the thesis, from the issuer's factsheet. If that share is below
  MIN_THESIS_SHARE, say what drives the rest.
- THIRD TIME NEEDS A SCORECARD: a third idea on the same ticker within
  REPEAT_WINDOW_DAYS must cite the scorecard of the earlier attempts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from kompas.core.scorecard import call_ideas

FLOOR_DAYS = 5
MIN_THESIS_SHARE = 0.60
REPEAT_WINDOW_DAYS = 60
MAX_ATTEMPTS = 2  # ideas allowed in the window before the scorecard must be cited
LIVE = ("naderend", "actief")


def _has_ticker(text: str, ticker: str) -> bool:
    return bool(re.search(rf"(?<![A-Z0-9]){re.escape(ticker.upper())}(?![A-Z0-9])", (text or "").upper()))


def playbook_blocks(ticker: str, playbooks: list[dict]) -> list[str]:
    """Keys of live playbooks with a "mijd" move on this ticker."""
    keys = []
    for p in playbooks:
        if p.get("status") not in LIVE:
            continue
        for m in (p.get("protect") or []) + (p.get("opportunity") or []):
            if m.get("action") == "mijd" and _has_ticker(m.get("what", "").split(" ")[0], ticker):
                keys.append(p.get("key", "?"))
                break
    return keys


def prior_attempts(ticker: str, calls: list[dict], today: str) -> list[str]:
    """Earlier separate ideas on this ticker within the window, as first-call
    timestamps. A run still going today is not counted as an earlier one."""
    end = date.fromisoformat(today[:10])
    found = []
    ideas = call_ideas(calls)
    for i, idea in enumerate(ideas):
        if not _has_ticker(idea.get("subject", ""), ticker):
            continue
        is_current_run = i == len(ideas) - 1
        age = (end - date.fromisoformat(idea["observed_at"][:10])).days
        if not is_current_run and 0 <= age <= REPEAT_WINDOW_DAYS:
            found.append(idea["observed_at"])
    return found


@dataclass(frozen=True)
class CallGuard:
    ticker: str
    is_fund: bool
    dip_call: bool  # is the why-now a drop in price?
    floor_days: int = 0  # Mila: trading days without a new closing low, from a sourced chart
    floor_source: str = ""
    drop_reason_resolved: str = ""  # or: the sourced fact that ended the drop's cause
    thesis_share: float | None = None  # funds: share of holdings that follows the thesis
    look_through: str = ""  # funds: what the share is made of, and what drives the rest, with the factsheet date
    scorecard_refs: list[str] = field(default_factory=list)  # scorecard docs of earlier attempts


def guard_errors(g: CallGuard, playbooks: list[dict], calls: list[dict], today: str) -> list[str]:
    errors: list[str] = []
    for key in playbook_blocks(g.ticker, playbooks):
        errors.append(f"{g.ticker}: het draaiboek {key} zegt 'mijd'; de call mag het niet tegenspreken")
    if g.dip_call:
        floor = g.floor_days >= FLOOR_DAYS and g.floor_source.strip()
        if not floor and not g.drop_reason_resolved.strip():
            errors.append(f"{g.ticker}: koopt op een daling zonder bodem (minder dan {FLOOR_DAYS} beursdagen "
                          "zonder nieuw slotdieptepunt) en zonder gebronnd feit dat de oorzaak wegnam: vallend mes")
    if g.is_fund:
        if g.thesis_share is None or not g.look_through.strip():
            errors.append(f"{g.ticker}: kijk door het fonds: welk deel volgt de these, volgens de factsheet?")
        elif g.thesis_share < MIN_THESIS_SHARE and "rest" not in g.look_through.lower():
            errors.append(f"{g.ticker}: slechts {g.thesis_share:.0%} volgt de these; zeg wat de rest drijft")
    earlier = prior_attempts(g.ticker, calls, today)
    if len(earlier) >= MAX_ATTEMPTS and not g.scorecard_refs:
        errors.append(f"{g.ticker}: al {len(earlier)} eerdere ideeën in {REPEAT_WINDOW_DAYS} dagen; "
                      "citeer hun scorekaart voor je het opnieuw voorstelt")
    return errors
