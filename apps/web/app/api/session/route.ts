import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const API = process.env.API_URL ?? "http://localhost:8000";

export async function GET() {
  const token = (await cookies()).get("samarthya_token")?.value;
  if (!token) return NextResponse.json({ user: null });
  try {
    const res = await fetch(`${API}/v1/me`, { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" });
    if (!res.ok) {
      const out = NextResponse.json({ user: null });
      if (res.status === 401) out.cookies.delete("samarthya_token");
      return out;
    }
    const u = await res.json();
    return NextResponse.json({ user: { email: u.email, role: u.role } });
  } catch {
    return NextResponse.json({ user: null, unavailable: true });
  }
}

export async function DELETE() {
  const out = NextResponse.json({ ok: true });
  out.cookies.delete("samarthya_token");
  return out;
}
