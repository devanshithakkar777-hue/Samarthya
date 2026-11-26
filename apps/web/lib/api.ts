import { notFound } from "next/navigation";

const API = process.env.API_URL ?? "http://localhost:8000";

export class ApiUnavailable extends Error {}

/** Server-side read of the public API. 404 becomes a Next not-found page; outages throw to the error page. */
export async function apiGet<T>(path: string, revalidate = 60): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, { next: { revalidate }, headers: { Accept: "application/json" } });
  } catch {
    throw new ApiUnavailable("The Samarthya service is not reachable right now.");
  }
  if (res.status === 404) notFound();
  if (!res.ok) throw new ApiUnavailable(`The Samarthya service returned an error (${res.status}).`);
  return (await res.json()) as T;
}

/** Same, but returns a fallback instead of throwing, for optional page sections. */
export async function apiTry<T>(path: string, fallback: T, revalidate = 60): Promise<T> {
  try {
    return await apiGet<T>(path, revalidate);
  } catch (e) {
    if (e instanceof ApiUnavailable) return fallback;
    throw e;
  }
}

export const apiBase = API;
