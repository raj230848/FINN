import math
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')

def percent_change(current: float | None, previous: float | None) -> float | None:
    """Signed change over absolute base. Negative bases are labelled in the UI."""
    if current is None or previous is None or previous == 0:
        return None
    if not all(math.isfinite(x) for x in (current, previous)):
        return None
    return round((current - previous) / abs(previous) * 100, 2)

def volume_ratio(current: int, history: list[int], lookback: int) -> float | None:
    if len(history) < lookback or current < 0:
        return None
    values = history[-lookback:]
    if any(x < 0 or not math.isfinite(x) for x in values):
        return None
    average = sum(values) / lookback
    return round(current / average, 2) if average > 0 else None

def complete_session(day, now: datetime | None = None) -> bool:
    now = (now or datetime.now(timezone.utc)).astimezone(IST)
    # Conservative delay after normal 15:30 close. The provider's returned
    # sessions, rather than a guessed weekday calendar, determine holidays.
    return day < now.date() or (day == now.date() and now.time() >= time(18, 30))

def guidance_comparison(low: float, high: float, actual: float) -> dict:
    if low > high or not all(math.isfinite(x) for x in (low, high, actual)):
        raise ValueError('Invalid guidance range or actual result')
    status = 'exceeded' if actual > high else 'missed' if actual < low else 'achieved'
    boundary = high if actual > high else low if actual < low else actual
    return {'status': status, 'deviation_pp': round(actual - boundary, 2), 'midpoint_deviation_pp': round(actual - (low + high) / 2, 2)}
