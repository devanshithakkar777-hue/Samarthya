export const KIND_LABEL: Record<string, string> = {
  degree: "University degree", diploma: "Diploma", certificate: "Certificate (ITI, NSQF, skill)",
  professional_qualification: "Professional qualification", certification: "Certification",
  licence: "Licence", examination: "Examination",
};
export const KIND_NOTE: Record<string, string> = {
  degree: "Awarded by a university or institution after a programme of study.",
  diploma: "A shorter vocational or technical programme.",
  certificate: "A trade or skill certificate, often NSQF-aligned.",
  professional_qualification: "Awarded by a professional body, not a university. Recognition varies.",
  certification: "An industry or vendor credential. Not equivalent to an accredited degree.",
  licence: "A permission to practise or operate, issued by a regulator.",
  examination: "An entrance, eligibility or recruitment examination. Not a qualification you study for in a course.",
};
export const STAGES: { id: string; label: string }[] = [
  { id: "after-10", label: "After Class 10" },
  { id: "after-12", label: "After Class 12" },
  { id: "pursuing", label: "Currently pursuing a degree" },
  { id: "graduate", label: "Graduate" },
  { id: "working", label: "Working professional" },
  { id: "research", label: "Research and higher studies" },
];
export const FIELD_LABEL: Record<string, string> = {
  training: "Mandatory training and work experience", cost_note: "Cost", official_url: "Official link",
  eligibility: "Eligibility", entry_route: "Entry route", syllabus: "Syllabus", recognition: "Recognition",
  cost_and_aid: "Cost and financial assistance", further_education: "Further education",
  alternative_pathways: "Alternative pathways", official_links: "Official links",
};
