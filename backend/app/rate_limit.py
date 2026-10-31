from collections import defaultdict, deque
from threading import Lock
from time import monotonic

_requests = defaultdict(deque)
_lock = Lock()

def allow_request(client, operation, limit, now=None):
    now = monotonic() if now is None else now
    with _lock:
        # Expire inactive clients too; arbitrary public IPs cannot grow the map forever.
        for key in list(_requests):
            if not _requests[key] or _requests[key][-1] <= now-60:
                del _requests[key]
        queue = _requests[(client,operation)]
        while queue and queue[0] <= now-60: queue.popleft()
        if len(queue)>=limit: return False
        queue.append(now)
        return True
