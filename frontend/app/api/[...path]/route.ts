import { NextRequest, NextResponse } from "next/server";

// One origin in the browser. Backend credentials remain on the server.
export const dynamic = "force-dynamic";
export const maxDuration = 60;
async function proxy(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
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
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("Content-Type") || "application/json",
        "Cache-Control": "no-store",
      },
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
