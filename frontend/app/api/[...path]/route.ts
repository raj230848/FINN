import { NextRequest, NextResponse } from "next/server";
import {
  requiresAccess,
  sameOrigin,
  SESSION_COOKIE,
  validSession,
} from "@/lib/server-auth";

// One origin in the browser. Backend credentials remain on the server.
export const dynamic = "force-dynamic";
export const maxDuration = 60;
async function proxy(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  if (requiresAccess()) {
    if (!process.env.FINN_API_TOKEN)
      return NextResponse.json(
        { detail: "The private desk is not configured." },
        { status: 503 },
      );
    if (!validSession(request.cookies.get(SESSION_COOKIE)?.value || "")) {
      return NextResponse.json(
        {
          detail: "Sign in to open your private FINN desk.",
          code: "SIGN_IN_REQUIRED",
        },
        { status: 401 },
      );
    }
    if (!["GET", "HEAD"].includes(request.method) && !sameOrigin(request)) {
      return NextResponse.json(
        { detail: "Invalid request origin." },
        { status: 403 },
      );
    }
  }
  const { path } = await params;
  const base = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(
    /\/$/,
    "",
  );
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (process.env.FINN_API_TOKEN)
    headers.Authorization = `Bearer ${process.env.FINN_API_TOKEN}`;
  try {
    const response = await fetch(
      `${base}/api/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
      {
        method: request.method,
        headers,
        cache: "no-store",
        body: ["GET", "HEAD"].includes(request.method)
          ? undefined
          : await request.text(),
        signal: AbortSignal.timeout(55000),
      },
    );
    const forwarded:Record<string,string>={"Content-Type":response.headers.get("Content-Type") || "application/json","Cache-Control":"no-store"};
    if(response.headers.get("Retry-After"))forwarded["Retry-After"]=response.headers.get("Retry-After")!;
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: forwarded,
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "FINN’s data service is unavailable or the request timed out. Check that the FastAPI backend is running on port 8000.",
      },
      { status: 503 },
    );
  }
}
export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH };
