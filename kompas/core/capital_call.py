"""Poort 1 -- the ONE EUR 100 answer per cycle, not N repeated ones.

Paul: "you can't just keep repeating to wait... make it a separate line.
If we (and by we I mean the team) had 100 to spend, take this. In the
end I will decide if I follow." That is a direct fix for a concrete
problem: capital_view used to live on every Signal and every Synthesis,
so a recap with twelve signals showed twelve near-identical "wacht"
verdicts. Each one was individually honest -- most subjects really
weren't actionable that day -- but the aggregate read as noise, and it
buried the one thing a daily recap actually needs to answer: if the
team weighs everything it saw this cycle TOGETHER, is there one real
idea worth naming?

CapitalCall is that single answer, built once per cycle after the
cycle's signals and syntheses are written -- never duplicated per item.
`considered` names what it weighed (subjects or signal/synthesis ids),
by reference, so nothing here re-states a Signal or Synthesis. Kelly
still pulls the trigger himself ("the meat in the seat") -- so does
Paul; this is exactly as hypothetical/non-executing as the old
per-signal capital_view was. A genuine "wacht" with no standout subject
is still a real answer and needs no `subject` -- this must never be
forced into naming something just to look decisive.

30/9/2026 -- what the question is. Paul: "The idea of the 100 eur move
is that my team feels opportunities and when asked what would you invest
your 100 eur now, what investment would that be." For two days the call
had drifted into rebalancing ("top up the sleeve that's furthest under
its range"), which turns every call into chasing the weights of what he
already owns -- a never-ending story. The call answers the opportunity
question: which investment, anywhere (an existing position, a name he
watches, or something new), is the best use of EUR 100 today, and why
now. The team's allocation (kompas/core/allocation.py) is only a
guardrail: `cap_check` can veto a call that pushes a theme past its cap,
it never picks the call. "wacht" stays legitimate only when a specific,
dated event is days away and the call names it.

6/10/2026 -- the amount is not literal. Paul: "je moet 100 euro niet
letterlijk nemen. wat als ik nu een potje had waarin zou ik investeren."
EUR 100 is shorthand for "money to put to work now", so a share priced
above EUR 100 is a valid answer; the call is about WHAT, not how much.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from kompas.core.signal import CAPITAL_VIEW_ACTIONS, CapitalView


@dataclass(frozen=True)
class CapitalCall:
    capital_view: CapitalView
    observed_at: str  # RFC3339
    considered: list[str] = field(default_factory=list)  # subjects/signal_ids weighed this cycle
    subject: str | None = None  # the name this call is about; None for a genuine "nothing stands out"


# Instruments Paul cannot buy at his brokers (MeDirect, Bolero), keyed by
# ticker, with the ISIN and the reason. A call naming one is useless to him,
# however good the thesis -- the gate rejects it so the team names a
# tradable alternative instead. Paul, 7/10/2026: "copx bestaat niet in
# medirect? wel in bolero maar is blijkbaar niet verhandelbaar door bepaalde
# kosten die door de emittent niet doorgegeven zijn" (no KID/cost data from
# the issuer, so a Belgian broker may not let him trade it).
KNOWN_UNTRADABLE: dict[str, tuple[str, str]] = {
    "COPX": (
        "IE0003Z9E2Y3",
        "Global X Copper Miners UCITS ETF: niet bij MeDirect; bij Bolero geblokkeerd "
        "omdat de uitgever geen kosteninformatie aanlevert",
    ),
}


def untradable_mentions(call: "CapitalCall") -> list[str]:
    """Tickers from KNOWN_UNTRADABLE that the call recommends: named as the
    subject, or their ISIN anywhere in the reasoning."""
    subject = call.subject or ""
    hits = []
    for ticker, (isin, _) in KNOWN_UNTRADABLE.items():
        if re.search(rf"\b{re.escape(ticker)}\b", subject) or isin in call.capital_view.reasoning:
            hits.append(ticker)
    return hits


@dataclass(frozen=True)
class CapitalCallValidationResult:
    ok: bool
    errors: list[str]


def validate_capital_call(call: CapitalCall) -> CapitalCallValidationResult:
    """The publication gate for the cycle's one capital call -- same
    discipline as validate_signal/validate_synthesis."""
    errors: list[str] = []

    if not call.observed_at.strip():
        errors.append("observed_at ontbreekt")

    if not call.considered:
        errors.append(
            "considered ontbreekt -- een capital call zonder vermelding van wat er "
            "afgewogen is, is niet controleerbaar"
        )

    cv = call.capital_view
    if cv.action not in CAPITAL_VIEW_ACTIONS:
        errors.append(f"capital_view.action {cv.action!r} is geen van {CAPITAL_VIEW_ACTIONS}")
    if not cv.reasoning.strip():
        errors.append("capital_view.reasoning ontbreekt")
    if not cv.trigger.strip():
        errors.append(
            "capital_view.trigger ontbreekt -- vooral bij 'wacht' verplicht: zonder een "
            "concrete voorwaarde is 'wacht' nooit fout, en dus geen echt standpunt"
        )
    if cv.action in ("nieuwe_positie", "verhoog_bestaand") and not (call.subject or "").strip():
        errors.append(
            f"capital_view {cv.action!r} vereist een subject -- een actie zonder naam "
            "is geen echt standpunt"
        )
    for ticker in untradable_mentions(call):
        isin, why = KNOWN_UNTRADABLE[ticker]
        errors.append(
            f"{ticker} ({isin}) is voor Paul niet verhandelbaar ({why}) -- "
            "kies een verhandelbaar alternatief op hetzelfde idee"
        )

    return CapitalCallValidationResult(ok=not errors, errors=errors)
