import { NextRequest, NextResponse } from "next/server";
import { BodyReadError,readSmallJson } from "@/lib/request-body";
import {
  createSession,
  matchesAccessToken,
  requiresAccess,
  sameOrigin,
  SESSION_COOKIE,
} from "@/lib/server-auth";

const attempts = new Map<string, { count: number; reset: number }>();
export async function POST(request: NextRequest) {
  if (!requiresAccess()) return NextResponse.json({ ok: true });
  if (!sameOrigin(request))
    return NextResponse.json(
      { detail: "Invalid sign-in origin." },
      { status: 403 },
    );
  // This is a single shared personal desk, not a multi-user account system.
  const now = Date.now();
  for (const [key, value] of attempts)
    if (value.reset < now) attempts.delete(key);
  // Avoid trusting a spoofable forwarding header for authentication throttling.
  const bucket = attempts.get("desk") || { count: 0, reset: now + 60000 };
  if (bucket.count >= 10)
    return NextResponse.json(
      { detail: "Please wait a minute before trying again." },
      { status: 429 },
    );
  bucket.count++;
  attempts.set("desk", bucket);
  try {
    const body = await readSmallJson(request);
    if (
      typeof body.access_code !== "string" ||
      !matchesAccessToken(body.access_code)
    ) {
      return NextResponse.json(
        { detail: "Incorrect access code." },
        { status: 401 },
      );
    }
    const response = NextResponse.json({ ok: true });
    response.cookies.set(SESSION_COOKIE, createSession(), {
      httpOnly: true,
      secure: request.nextUrl.protocol === "https:",
      sameSite: "strict",
      path: "/",
      maxAge: 8 * 60 * 60,
    });
    return response;
  } catch (error) {
    if(error instanceof BodyReadError)return NextResponse.json({detail:error.message},{status:error.status});
    return NextResponse.json(
      {
        detail:
          "Sign-in is unavailable. Check the server access configuration.",
      },
      { status: 503 },
    );
  }
}
export async function DELETE(request: NextRequest) {
  if (!sameOrigin(request))
    return NextResponse.json({ detail: "Invalid origin." }, { status: 403 });
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}
