"""Seasonality computed from monthly volumes - arithmetic only.

- profile: mean volume per calendar month over the last full years (up to 3), as a share of the
  overall mean. 1.0 = an average month; 1.6 = 60% above average.
- peak / low months: the calendar months with the highest and lowest profile value.
- seasonality_index: max profile / min profile. Around 1.2 is flat; 2 or more is clearly seasonal.
- yoy_change: sum of the last 12 months against the 12 before them.
Months with unknown volume are left out, never counted as zero.
"""
from __future__ import annotations

YEARS = 3


def seasonality(monthly: list[dict]) -> dict:
    known = [m for m in monthly if m.get("volume") is not None]
    if len(known) < 12:
        return {"months": len(known)}
    recent = known[-12 * YEARS:]
    by_month: dict[int, list[int]] = {}
    for m in recent:
        by_month.setdefault(m["month"], []).append(m["volume"])
    means = {month: sum(v) / len(v) for month, v in by_month.items()}
    overall = sum(means.values()) / len(means)
    profile = {month: round(value / overall, 3) if overall else None for month, value in sorted(means.items())}
    valid = {k: v for k, v in profile.items() if v is not None}
    last12 = sum(m["volume"] for m in known[-12:])
    prev12 = sum(m["volume"] for m in known[-24:-12]) if len(known) >= 24 else None
    low = min(valid.values()) if valid else None
    return {
        "months": len(known),
        "profile": profile,
        "peak_month": max(valid, key=valid.get) if valid else None,
        "low_month": min(valid, key=valid.get) if valid else None,
        "seasonality_index": round(max(valid.values()) / low, 2) if valid and low else None,
        "yoy_change": round(last12 / prev12 - 1, 3) if prev12 else None,
    }
