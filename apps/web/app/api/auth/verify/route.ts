import { NextRequest, NextResponse } from "next/server";

const API = process.env.API_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  let res: Response;
  try {
    res = await fetch(`${API}/v1/auth/otp/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-forwarded-for": req.headers.get("x-forwarded-for") ?? "" },
      body: await req.text(),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "The Samarthya service is not reachable right now." }, { status: 502 });
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return NextResponse.json({ detail: data.detail ?? "Could not sign in" }, { status: res.status });
  const out = NextResponse.json({ user: data.user });
  out.cookies.set("samarthya_token", data.token, {
    httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 60 * 60 * 24 * 7,
  });
  return out;
}
