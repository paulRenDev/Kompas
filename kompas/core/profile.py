"""What Paul told the team about himself -- the yardstick for "ontwrichtend".

Paul, 16/11/2026, asked by Farah for his pain threshold: "pijngrens 20% Kan
zijn dat ik soms geld nodig heb, maar dat is het risico dat ik neem. zo
weinig mogelijk laten we zeggen maar tegenslagen bestaan".

So a scenario's disruption score is no longer Farah's feeling. It is the
estimated drop of the WHOLE portfolio if the scenario happens, measured
against PAIN_LIMIT. A 5 means the scenario alone would take him to his pain
threshold.
"""

from __future__ import annotations

PAIN_LIMIT = 0.20  # the drop of the whole portfolio Paul accepts before it hurts
CASH_NEED = "zelden, maar het kan; Paul draagt dat risico zelf"

# Upper bounds (as a share of the portfolio) for disruption 1..4; 5 is anything
# at or over the pain limit. 1 is under a tenth of the limit, 4 is up to it.
DISRUPTION_BANDS = (0.02, 0.05, 0.10, PAIN_LIMIT)


def disruption_for(impact: float) -> int:
    """Disruption 1-5 for an estimated drop of the whole portfolio (0.035 = 3.5%)."""
    for score, upper in enumerate(DISRUPTION_BANDS, start=1):
        if impact < upper:
            return score
    return 5
