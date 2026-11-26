"use client";

import { useState } from "react";
import Crud from "@/components/kit/Crud";
import { Tabs } from "@/components/kit/Controls";
import Decks from "./Decks";
import Planner from "./Planner";

export default function StudyTabs() {
  const [tab, setTab] = useState("notes");
  return (
    <>
      <Tabs label="Study tools" value={tab} onChange={setTab} tabs={[{ key: "notes", label: "Notes" }, { key: "cards", label: "Flashcards" }, { key: "plan", label: "Study planner" }]} />
      {tab === "notes" && (
        <Crud path="/v1/me/notes" noun="note" empty="No notes yet. Write one, or take a note from any lesson."
          fields={[{ name: "title", label: "Title", required: true }, { name: "folder", label: "Folder (optional)" }, { name: "body", label: "Note", type: "textarea", rows: 8 }]}
          render={(r) => (<><h3 className="font-semibold">{String(r.title)}</h3>{r.folder ? <p className="text-xs text-slate">{String(r.folder)}</p> : null}<p className="mt-2 whitespace-pre-line text-sm">{String(r.body ?? "")}</p></>)} />
      )}
      {tab === "cards" && <Decks />}
      {tab === "plan" && <Planner />}
    </>
  );
}
