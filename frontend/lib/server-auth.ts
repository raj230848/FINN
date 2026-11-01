import { createHmac, timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "finn_session";
export function requiresAccess() {
  return (
    process.env.FINN_PUBLIC_MODE === "true" ||
    process.env.VERCEL === "1" ||
    process.env.RENDER === "true"
  );
}
function secret() {
  const value = process.env.FINN_SESSION_SECRET || "";
  if (value.length < 32) throw new Error("Access control is not configured.");
  return value;
}
export function matchesAccessToken(input: string) {
  const expected = process.env.FINN_ACCESS_TOKEN || "";
  if (expected.length < 16 || input.length > 512) return false;
  const a = createHmac("sha256", secret()).update(input).digest();
  const b = createHmac("sha256", secret()).update(expected).digest();
  return timingSafeEqual(a, b);
}
export function createSession(now = Date.now()) {
  const payload = Buffer.from(
    JSON.stringify({ exp: now + 8 * 60 * 60 * 1000 }),
  ).toString("base64url");
  return `${payload}.${createHmac("sha256", secret())
    .update(payload + ":" + (process.env.FINN_ACCESS_TOKEN || ""))
    .digest("base64url")}`;
}
export function validSession(value: string, now = Date.now()) {
  try {
    if ((process.env.FINN_ACCESS_TOKEN || "").length < 16 || value.length > 512)
      return false;
    const [payload, signature, ...extra] = value.split(".");
    if (!payload || !signature || extra.length) return false;
    const expected = createHmac("sha256", secret())
      .update(payload + ":" + (process.env.FINN_ACCESS_TOKEN || ""))
      .digest();
    const provided = Buffer.from(signature, "base64url");
    if (
      provided.length !== expected.length ||
      !timingSafeEqual(expected, provided)
    )
      return false;
    const exp = JSON.parse(Buffer.from(payload, "base64url").toString()).exp;
    return Number.isFinite(exp) && exp > now && exp <= now + 8 * 60 * 60 * 1000;
  } catch {
    return false;
  }
}
export function sameOrigin(request: Request) {
  const origin = request.headers.get("origin");
  const url = new URL(request.url);
  // Next may normalize its internal URL to localhost; Host retains the
  // browser-facing authority. Do not trust arbitrary forwarded-host headers.
  const host = request.headers.get("host");
  return Boolean(origin) && origin === (host ? `${url.protocol}//${host}` : url.origin);
}
