"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, call } from "./client";

/** Loads one signed-in resource and exposes reload. 401 is reported as `needsSignIn`, never as a crash. */
export function useMine<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [needsSignIn, setNeedsSignIn] = useState(false);
  const [loading, setLoading] = useState(!!path);
  const load = useCallback(async () => {
    if (!path) return;
    setLoading(true);
    try { setData(await call<T>("GET", path)); setError(""); setNeedsSignIn(false); }
    catch (e) {
      if (e instanceof ApiError && e.status === 401) setNeedsSignIn(true);
      else setError((e as Error).message);
    } finally { setLoading(false); }
  }, [path]);
  useEffect(() => { void load(); }, [load]);
  return { data, error, needsSignIn, loading, reload: load, setData };
}

/** Runs a write and reports a plain-language error. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true); setError("");
    try { return await fn(); } catch (e) { setError((e as Error).message); return undefined; } finally { setBusy(false); }
  }
  return { busy, error, run, setError };
}
