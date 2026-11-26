"use client";

import { useState } from "react";
import { inp } from "@/components/kit/Controls";

const OCCASIONS: Record<string, { label: string; items: string[] }> = {
  interview: { label: "Job or internship interview", items: ["Ask the recruiter if there is a dress code. If there is none, choose what is neat and suits the workplace.", "Clothes are clean, ironed or smoothed, and comfortable to sit and walk in.", "Footwear is clean and comfortable.", "Carry copies of your resume, a pen, a notebook and your ID in a bag that closes.", "Plan the journey and leave early enough to arrive calm.", "Keep your phone on silent and out of reach."] },
  video: { label: "Video interview or online meeting", items: ["Test camera, microphone and internet before the call; keep a phone hotspot as a backup.", "Sit facing a window or lamp so your face is lit from the front.", "Check what is visible behind you and tidy it, or use a plain background.", "Wear something neat from the waist up and from the waist down in case you stand.", "Close other apps and mute notifications.", "Keep a glass of water and your notes out of the camera view."] },
  presentation: { label: "Presentation or viva", items: ["Wear something you can move and breathe in. Comfort helps you think.", "Rehearse out loud at least once, with a timer.", "Save the file in two places and carry it on a drive or have it online.", "Reach early to check the screen, cables and your slides.", "Have water and a printed copy of your key points."] },
  gd: { label: "Group discussion", items: ["Wear what is neat and fits the setting.", "Carry a pen and a small notebook for points.", "Arrive early, greet people, and take a seat where you can see everyone.", "Plan one opening point and one question to ask others."] },
  first_day: { label: "First day at a workplace", items: ["Ask your manager or HR what the dress code and start time are.", "Carry your ID proof, bank and joining documents as asked.", "Know your route and the person you should ask for at the gate.", "Bring a notebook, a pen and water.", "Plan to introduce yourself to people in one sentence."] },
  networking: { label: "Networking event or career fair", items: ["Wear something neat that suits the event; ask the organiser if unsure.", "Prepare a two-sentence introduction about who you are and what you are looking for.", "Carry a few copies of your resume or a QR link to your profile.", "Decide two or three people or stalls you most want to meet.", "Follow up with a short thank-you message within two days."] },
};
/** Neatness and appropriateness only. Nothing here rates anyone's looks, body, skin, hair or traditional dress. */
export default function Presence() {
  const [k, setK] = useState("interview");
  const [done, setDone] = useState<Record<string, boolean>>({});
  const o = OCCASIONS[k];
  return (
    <div className="max-w-2xl grid gap-4">
      <p className="rounded-md bg-ice-blue/40 p-3 text-sm">There is no single right look. Neat, clean, comfortable and suited to the setting is enough, and traditional or cultural dress is fine wherever it is neat and suitable. You never need to spend money to be taken seriously. Ticks stay on this page only.</p>
      <div><label htmlFor="occ" className="font-medium">Occasion</label><select id="occ" className={inp} value={k} onChange={(e) => setK(e.target.value)}>{Object.entries(OCCASIONS).map(([key, v]) => <option key={key} value={key}>{v.label}</option>)}</select></div>
      <ul className="grid gap-2">{o.items.map((t, i) => <li key={k + i}><label className="flex items-start gap-3 rounded-md border border-ink/10 bg-white p-3"><input type="checkbox" className="mt-1" checked={!!done[k + i]} onChange={(e) => setDone({ ...done, [k + i]: e.target.checked })} /><span>{t}</span></label></li>)}</ul>
      <p className="text-sm text-slate">Draft guidance, pending review by a counsellor or placement officer.</p>
    </div>
  );
}
