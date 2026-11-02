import { NextRequest, NextResponse } from "next/server";
import {backendTimeoutMs} from "@/lib/proxy-policy";
import {
  requiresAccess,
  sameOrigin,
  SESSION_COOKIE,
  validSession,
} from "@/lib/server-auth";

// One origin in the browser. Backend credentials remain on the server.
export const dynamic = "force-dynamic";
export const maxDuration = 180;
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
        signal: AbortSignal.timeout(backendTimeoutMs(request.method,path)),
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
          request.method==="POST"&&path.length===1&&path[0]==="documents"
            ? "The document service did not respond in time. An import may still finish on the server. Check Source library before retrying; saved documents remain available."
            : "FINN’s data service is temporarily unavailable or the request timed out. Please try again. Saved data will be available when the service returns.",
      },
      { status: 503 },
    );
  }
}
export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH };
