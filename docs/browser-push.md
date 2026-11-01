# Optional browser delivery

FINN retains in-app history without external delivery. To enable Web Push on the full Python application:

```powershell
.\.venv\Scripts\python.exe scripts/configure-push.py --subject mailto:YOUR_REAL_CONTACT@example.com
```

This creates keys only in the ignored root `.env`, without printing them. Use your actual contact. Existing keys are preserved. On a host, store `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` and `VAPID_SUBJECT` in backend runtime secrets, then restart one backend worker. The public key is returned to the browser; the private key remains server-only. Optional delivery processing runs every 30 seconds even if source scheduling is off.

Open Notifications → Enable browser alerts on a supported secure browser, grant permission and keep the device subscription. Opt-in is device-specific. On iPhone, a compatible installed home-screen web app may be required. Unsupported environments keep in-app notifications. The static Sites demo has no Python delivery worker.

Only newly observed sourced events after opt-in qualify. Watchlist/company/category and price/volume settings are checked when queued and again before delivery. Old history and demo scenarios are not replayed. Disable browser alerts to deactivate the server recipient and cancel pending sends, then unsubscribe the device. Revoked/expired subscriptions (404/410) are disabled automatically.

The durable outbox uses atomic claims, bounded retries and sanitized status codes. Subscription endpoints and cryptographic keys are private database fields, excluded from responses/logs and source exports. Browser-provider endpoints are restricted to supported services. Recipient delivery timestamps mean the push provider accepted the message; they do not prove that a phone displayed it. Stable event tags and IndexedDB receipts suppress repeated display after a retry. Delivery is best effort, not an instantaneous intraday feed or an exactly-once network guarantee.

Controlled sender tests passed; a real opt-in and device display have not been verified in this environment. No notification permission is requested automatically on page load.

References: [pywebpush](https://github.com/web-push-libs/pywebpush), [browser subscription API](https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe).
