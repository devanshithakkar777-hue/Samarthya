"use client";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

/** Browser calls always go to our own origin; the proxy adds the sign-in cookie. */
export async function call<T>(method: string, path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/proxy${path}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "You appear to be offline. Please check your connection and try again.");
  }
  const text = await res.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* non-JSON error body */ }
  if (!res.ok) {
    const d = (data as { detail?: unknown } | null)?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? "Some details were not valid. Please check and try again." : "Something went wrong. Please try again.";
    throw new ApiError(res.status, msg);
  }
  return data as T;
}
