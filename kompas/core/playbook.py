"""Playbooks -- "what if" events, written down before they happen.

Paul, 19/10/2026, after the team admitted only the AI bubble had a written
plan: "ik zou dynamische draaiboeken willen afhankelijk van nieuws. wat als
trump senaat en house verliest? wat als rusland zijn view opdringt, wat als
le pen wint of net niet, wat als de eu begroting zwaar tegenvalt wat als us
weer rare claims legt op groenland, wat als er een significante klimaatramp
optreedt [...] what if what if what if." And the goal, in his words:
"ongeschonden en liefst beter uitkomen".

So every playbook has two halves, both required: what protects him
(`protect`) and where the win is (`opportunity`). "Dynamic" means the
evening cycle keeps them alive: it moves a playbook from waakzaam to
naderend when a dated moment comes close or its watch signals move, to
actief when the event actually happens (a sourced fact, never a mood), and
to voorbij once it has passed. It may add a new playbook when the news
throws up a genuinely new what-if, and retire stale ones.

Two limits keep "what if" from turning into "panic about everything":
- MAX_LIVE playbooks at a time; a new one means an old one gets retired;
- a playbook that turns actief may move at most `shift_max` of the
  portfolio (never more than MAX_SHIFT), through a sell proposal with source
  "draaiboek" (kompas/core/sell_proposal.py), and always with an undo rule.
Everything stays hypothetical and non-executing: Paul trades himself.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kompas.core.capital_call import KNOWN_UNTRADABLE
from kompas.core.scenario_monitor import SCENARIOS

STATUSES = ("waakzaam", "naderend", "actief", "voorbij")
MOVE_ACTIONS = ("koop", "verkoop", "houd", "mijd")
MAX_SHIFT = 0.20  # the most one active playbook may move, as a share of the portfolio
MAX_LIVE = 10  # playbooks that are not "voorbij"


@dataclass(frozen=True)
class Move:
    action: str  # one of MOVE_ACTIONS
    what: str  # an instrument (ticker) or a plainly named group, e.g. "Europese banken"
    why: str


@dataclass(frozen=True)
class Playbook:
    key: str
    what_if: str  # the event, in Paul's terms
    when: str  # the dated moment, or what would make it happen
    status: str  # one of STATUSES
    status_reason: str  # the sourced fact behind the status
    source: str
    watch: list[str]  # leading signals the team checks
    protect: list[Move]  # how Paul stays unharmed
    opportunity: list[Move]  # how he comes out better
    shift_max: float  # share of the portfolio this playbook may move when actief
    undo: str  # what makes the team move back
    updated_at: str  # RFC3339
    scenario_links: list[str] = field(default_factory=list)  # keys in SCENARIOS


@dataclass(frozen=True)
class PlaybookValidationResult:
    ok: bool
    errors: list[str]


def validate_playbook(p: Playbook) -> PlaybookValidationResult:
    errors: list[str] = []
    if not p.key.strip() or p.key != p.key.strip().lower() or " " in p.key:
        errors.append("key moet een korte id zijn zonder spaties, in kleine letters")
    if p.status not in STATUSES:
        errors.append(f"status {p.status!r} is geen van {STATUSES}")
    for name, text in (("what_if", p.what_if), ("when", p.when), ("status_reason", p.status_reason),
                       ("source", p.source), ("undo", p.undo), ("updated_at", p.updated_at)):
        if not text.strip():
            errors.append(f"{name} ontbreekt")
    if not p.watch:
        errors.append("geen signalen om op te letten -- dan is het geen draaiboek maar een gok")
    if not p.protect:
        errors.append("geen bescherming: Paul wil ongeschonden uitkomen")
    if not p.opportunity:
        errors.append("geen kans: Paul wil er liefst beter uitkomen")
    for m in p.protect + p.opportunity:
        if m.action not in MOVE_ACTIONS:
            errors.append(f"{m.what}: actie {m.action!r} is geen van {MOVE_ACTIONS}")
        if not m.what.strip() or not m.why.strip():
            errors.append("een stap zonder wat of waarom")
        if m.what.strip().upper() in KNOWN_UNTRADABLE:
            errors.append(f"{m.what}: staat op de lijst van niet verhandelbare producten")
    if not 0 <= p.shift_max <= MAX_SHIFT:
        errors.append(f"shift_max {p.shift_max} valt buiten 0 tot {MAX_SHIFT}")
    unknown = [k for k in p.scenario_links if k not in SCENARIOS]
    if unknown:
        errors.append(f"onbekende scenario's: {unknown}")
    return PlaybookValidationResult(ok=not errors, errors=errors)


def live_count(playbooks: list[Playbook]) -> int:
    return sum(p.status != "voorbij" for p in playbooks)


def max_shift_eur(p: Playbook, value_by_ticker: dict[str, float]) -> float:
    """What an active playbook may move, in euros, from the live wallet."""
    if p.status != "actief":
        return 0.0
    return round(min(p.shift_max, MAX_SHIFT) * sum(value_by_ticker.values()), 2)
