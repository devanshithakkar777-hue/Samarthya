import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API = process.env.API_URL ?? "http://localhost:8000";
// Never forwarded: the sign-in verify call is handled by /api/auth/verify so the token stays in an httpOnly cookie.
const BLOCKED = [/^v1\/auth\/otp\/verify$/];

async function forward(req: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const joined = path.join("/");
  if (!joined.startsWith("v1/") || joined.includes("..") || BLOCKED.some((r) => r.test(joined))) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }
  const token = (await cookies()).get("samarthya_token")?.value;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) headers["x-forwarded-for"] = fwd;
  let body: string | undefined;
  if (!["GET", "HEAD"].includes(req.method)) {
    body = await req.text();
    headers["Content-Type"] = "application/json";
  }
  try {
    const res = await fetch(`${API}/${joined}${req.nextUrl.search}`, { method: req.method, headers, body, cache: "no-store" });
    const type = res.headers.get("content-type") ?? "application/json";
    const out: Record<string, string> = { "Content-Type": type, "Cache-Control": "no-store" };
    const disposition = res.headers.get("content-disposition");
    if (disposition) out["Content-Disposition"] = disposition;
    // files (resume exports, transcript, calendar) pass through as bytes; everything else stays text
    if (disposition || /^(application\/(pdf|vnd\.|octet)|text\/calendar)/.test(type)) {
      return new NextResponse(await res.arrayBuffer(), { status: res.status, headers: out });
    }
    const text = await res.text();
    return new NextResponse(text || null, { status: res.status, headers: out });
  } catch {
    return NextResponse.json({ detail: "The Samarthya service is not reachable right now." }, { status: 502 });
  }
}

export { forward as GET, forward as POST, forward as PUT, forward as PATCH, forward as DELETE };
