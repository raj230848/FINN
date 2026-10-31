import test from "node:test";
import assert from "node:assert/strict";
import {
  createSession,
  validSession,
  matchesAccessToken,
  requiresAccess,
  sameOrigin,
} from "../lib/server-auth.ts";

test("protected desk cookies reject tampering, expiry and rotated access codes", () => {
  const old = { ...process.env };
  try {
    process.env.FINN_SESSION_SECRET =
      "a-test-session-secret-with-at-least-32-characters";
    process.env.FINN_ACCESS_TOKEN =
      "a-test-access-code-with-more-than-16-characters";
    process.env.FINN_PUBLIC_MODE = "true";
    const now = Date.now(),
      cookie = createSession(now);
    assert.equal(requiresAccess(), true);
    assert.equal(matchesAccessToken(process.env.FINN_ACCESS_TOKEN), true);
    assert.equal(matchesAccessToken("incorrect"), false);
    assert.equal(validSession(cookie, now), true);
    assert.equal(validSession(cookie + "tamper", now), false);
    assert.equal(validSession(cookie, now + 8 * 60 * 60 * 1000 + 1), false);
    assert.equal(validSession("not-a-session", now), false);
    process.env.FINN_ACCESS_TOKEN = "a-different-test-code-long-enough";
    assert.equal(validSession(cookie, now), false);
    delete process.env.FINN_SESSION_SECRET;
    assert.equal(validSession(cookie, now), false);
  } finally {
    for (const key of Object.keys(process.env))
      if (!(key in old)) delete process.env[key];
    Object.assign(process.env, old);
  }
});

test("cross-origin mutations are rejected", () => {
  assert.equal(sameOrigin(new Request("http://localhost:3003/api/session", {
    headers: { host: "127.0.0.1:3003", origin: "http://127.0.0.1:3003" },
  })), true);
  assert.equal(sameOrigin(new Request("https://finn.example/api/session", {
    headers: { host: "finn.example", origin: "https://evil.example", "x-forwarded-host": "evil.example" },
  })), false);
  assert.equal(
    sameOrigin(
      new Request("https://finn.example/api/research", {
        headers: { origin: "https://finn.example" },
      }),
    ),
    true,
  );
  assert.equal(
    sameOrigin(
      new Request("https://finn.example/api/research", {
        headers: { origin: "https://malicious.example" },
      }),
    ),
    false,
  );
  assert.equal(
    sameOrigin(new Request("https://finn.example/api/research")),
    false,
  );
});
