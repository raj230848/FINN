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
export function browserOrigin(request: Request): string | null {
  // Explicit server config is authoritative behind HTTPS-terminating proxies.
  // Never infer the external origin from arbitrary forwarded headers.
  const configured = process.env.FINN_PUBLIC_ORIGIN || process.env.RENDER_EXTERNAL_URL;
  if (configured) {
    try {
      const target = new URL(configured);
      if (target.username || target.password || target.search || target.hash || target.pathname !== "/" || (target.protocol !== "https:" && !(target.protocol === "http:" && ["127.0.0.1", "localhost"].includes(target.hostname)))) return null;
      return target.origin;
    } catch { return null; }
  }
  const url = new URL(request.url);
  const host = request.headers.get("host");
  return host ? `${url.protocol}//${host}` : url.origin;
}
export function sameOrigin(request: Request) {
  const expected = browserOrigin(request);
  return Boolean(expected) && request.headers.get("origin") === expected;
}
