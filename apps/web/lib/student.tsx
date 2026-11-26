"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError, call } from "./client";
import type { FitItem, Profile } from "./types";

const KEY = "samarthya.student.v1";
export const EMPTY: Profile = { qualification: null, year_of_study: null, expected_graduation_year: null, interests: [], skills: [] };

type Local = { profile: Profile; completed: number[] };
type SessionUser = { email: string; role: string } | null;

type Ctx = {
  ready: boolean;
  user: SessionUser;
  profile: Profile;
  completed: number[];
  hasProfile: boolean;
  saveProfile: (p: Profile) => Promise<void>;
  setRequirement: (id: number, done: boolean) => Promise<void>;
  loadFit: (sort: "eligibility" | "compatibility" | "readiness") => Promise<FitItem[]>;
  signedIn: (user: NonNullable<SessionUser>) => Promise<void>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<void>;
  clearLocal: () => void;
};

const StudentCtx = createContext<Ctx | null>(null);

function readLocal(): Local {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const v = JSON.parse(raw);
      return { profile: { ...EMPTY, ...v.profile }, completed: Array.isArray(v.completed) ? v.completed : [] };
    }
  } catch { /* storage blocked or corrupt: start empty */ }
  return { profile: EMPTY, completed: [] };
}
function writeLocal(l: Local) {
  try { localStorage.setItem(KEY, JSON.stringify(l)); } catch { /* storage blocked: keep in memory only */ }
}

export function StudentProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<SessionUser>(null);
  const [profile, setProfile] = useState<Profile>(EMPTY);
  const [completed, setCompleted] = useState<number[]>([]);

  const loadAccount = useCallback(async () => {
    const data = await call<{ profile: Profile; checklist: { requirement_id: number; status: string }[] }>("GET", "/v1/me/export");
    setProfile({ ...EMPTY, ...data.profile });
    setCompleted(data.checklist.filter((c) => c.status === "done").map((c) => c.requirement_id));
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const s = await fetch("/api/session", { cache: "no-store" }).then((r) => r.json());
        if (!alive) return;
        if (s.user) { setUser(s.user); await loadAccount(); }
        else { const l = readLocal(); setProfile(l.profile); setCompleted(l.completed); }
      } catch {
        const l = readLocal(); setProfile(l.profile); setCompleted(l.completed);
      } finally { if (alive) setReady(true); }
    })();
    return () => { alive = false; };
  }, [loadAccount]);

  const saveProfile = useCallback(async (p: Profile) => {
    setProfile(p);
    if (user) await call("PUT", "/v1/me/profile", p);
    else writeLocal({ profile: p, completed });
  }, [user, completed]);

  const setRequirement = useCallback(async (id: number, done: boolean) => {
    const next = done ? Array.from(new Set([...completed, id])) : completed.filter((x) => x !== id);
    setCompleted(next);
    try {
      if (user) await call("PUT", `/v1/me/checklist/items/${id}`, { status: done ? "done" : "todo" });
      else writeLocal({ profile, completed: next });
    } catch (e) {
      setCompleted(completed); // roll back so the screen never shows progress that was not saved
      throw e;
    }
  }, [user, completed, profile]);

  const loadFit = useCallback(async (sort: "eligibility" | "compatibility" | "readiness") => {
    if (user) return (await call<{ results: FitItem[] }>("GET", `/v1/me/fit?sort=${sort}`)).results;
    const body = {
      profile: { qualification: profile.qualification, year_of_study: profile.year_of_study,
        expected_graduation_year: profile.expected_graduation_year, interests: profile.interests, skills: profile.skills },
      completed_requirement_ids: completed, sort,
    };
    return (await call<{ results: FitItem[] }>("POST", "/v1/fit", body)).results;
  }, [user, profile, completed]);

  const signedIn = useCallback(async (u: NonNullable<SessionUser>) => {
    // carry what the student already did on this device into the new account
    const local = readLocal();
    setUser(u);
    try {
      const existing = await call<{ profile: Profile }>("GET", "/v1/me/export");
      const hasServer = !!existing.profile.qualification || existing.profile.interests.length > 0;
      if (!hasServer && (local.profile.qualification || local.profile.interests.length)) {
        await call("PUT", "/v1/me/profile", local.profile);
        for (const id of local.completed) {
          try { await call("PUT", `/v1/me/checklist/items/${id}`, { status: "done" }); }
          catch (e) { if (!(e instanceof ApiError && e.status === 404)) throw e; }
        }
      }
    } finally {
      await loadAccount();
      try { localStorage.removeItem(KEY); } catch { /* ignore */ }
    }
  }, [loadAccount]);

  const signOut = useCallback(async () => {
    await fetch("/api/session", { method: "DELETE" });
    setUser(null); setProfile(EMPTY); setCompleted([]);
  }, []);

  const deleteAccount = useCallback(async () => {
    await call("DELETE", "/v1/me");
    await fetch("/api/session", { method: "DELETE" });
    setUser(null); setProfile(EMPTY); setCompleted([]);
  }, []);

  const clearLocal = useCallback(() => {
    try { localStorage.removeItem(KEY); } catch { /* ignore */ }
    setProfile(EMPTY); setCompleted([]);
  }, []);

  const value = useMemo<Ctx>(() => ({
    ready, user, profile, completed, hasProfile: !!profile.qualification || profile.interests.length > 0,
    saveProfile, setRequirement, loadFit, signedIn, signOut, deleteAccount, clearLocal,
  }), [ready, user, profile, completed, saveProfile, setRequirement, loadFit, signedIn, signOut, deleteAccount, clearLocal]);

  return <StudentCtx.Provider value={value}>{children}</StudentCtx.Provider>;
}

export function useStudent(): Ctx {
  const c = useContext(StudentCtx);
  if (!c) throw new Error("useStudent must be used inside StudentProvider");
  return c;
}
