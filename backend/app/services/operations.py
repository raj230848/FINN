"""Bounded process metrics and restart recovery; no request bodies or secrets."""
from collections import Counter
from datetime import datetime, timezone
from threading import Lock

from sqlalchemy import select
from ..models import SyncRun, utcnow


class ProcessMetrics:
    def __init__(self):
        self._lock = Lock()
        self._counts = Counter()
        self._last = {}
        self.started_at = datetime.now(timezone.utc).isoformat()

    def record(self, component, outcome, *, duration_ms=None, tokens=None, attempts=None):
        if component not in {'gemini', 'api'} or outcome not in {'success', 'not_configured', 'input_limit', 'timeout', 'rate_limited', 'rejected', 'invalid_response', 'error', 'unauthorized'}:
            return
        values = {'outcome': outcome, 'at': datetime.now(timezone.utc).isoformat()}
        for name, value in [('duration_ms', duration_ms), ('tokens', tokens), ('attempts', attempts)]:
            if type(value) is int and 0 <= value <= 1_000_000_000:
                values[name] = value
        with self._lock:
            self._counts[component + '.' + outcome] += 1
            self._last[component] = values

    def snapshot(self):
        with self._lock:
            return {'scope': 'current process; counters reset on restart', 'started_at': self.started_at, 'counts': dict(self._counts), 'last': {k: dict(v) for k, v in self._last.items()}}


metrics = ProcessMetrics()


def recover_interrupted_syncs(db):
    """One worker owns sync jobs. Preserve partial successes and expose interruption."""
    count = 0
    for run in db.scalars(select(SyncRun).where(SyncRun.completed_at.is_(None))):
        run.result = {**(run.result or {}), 'status': 'interrupted', 'message': 'The service restarted before this refresh completed. Saved source data remains available. Start a new refresh to continue.'}
        run.completed_at = utcnow()
        count += 1
    db.flush()
    return count
