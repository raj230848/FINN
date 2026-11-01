// Public, minimal host readiness. No desk data, credentials or internal URL.
export const dynamic = "force-dynamic";
export async function GET() {
  const base = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
  try {
    const response = await fetch(`${base}/api/health`, {cache:"no-store", signal:AbortSignal.timeout(4000)});
    if (!response.ok || (await response.json()).status !== "ok") throw new Error("Not ready");
    return Response.json({status:"ready"}, {headers:{"Cache-Control":"no-store"}});
  } catch {
    return Response.json({status:"unavailable"}, {status:503, headers:{"Cache-Control":"no-store"}});
  }
}
