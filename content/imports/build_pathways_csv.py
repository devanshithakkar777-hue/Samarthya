"""Turns the Samarthya Education & Qualification Directory brief (pathways_brief.md) into a draft-import CSV.
Each bullet under a numbered stream section becomes one row. Nothing is added beyond the brief's own wording."""
import csv, re
STREAMS = {1:"Science (PCM)",2:"Science (PCB)",3:"Science (PCMB)",4:"Commerce",5:"Humanities and Arts",6:"Vocational",
 7:"Engineering and Technology",8:"Medical and Health Sciences",9:"Agriculture and Environment",10:"Law",
 11:"Management and Business",12:"Finance, Banking and Economics",13:"Architecture, Planning and Design",
 14:"Arts, Media and Entertainment",15:"Education, Public Policy and Public Service"}
SRC = dict(source_url="https://samarthya.example/briefs/education-pathways-directory",
           source_title="Samarthya Education and Qualification Directory brief (reviewed by the project team)",
           source_publisher="Samarthya project team", source_kind="third_party")
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:80].strip("-")
def kind_level(h, name):
    h=h.lower(); n=name.lower()
    if "certificat" in h and "professional" in h or h.startswith("professional cert") or "certifications" in h and "skill" not in h: k="certification"
    elif "professional qualifications" in h or "additional professional" in h or "professional and specialist" in h or "professional and competitive" in h or "professional and" in h and "pathways" in h: k="professional_qualification"
    elif "iti" in h or "skill-sector" in h: k="certificate"
    elif "diploma" in h or n.startswith(("diploma","d.pharm","d.el.ed")): k="diploma"
    elif "examination" in n or n.endswith(("exam","examinations")) or n in ("aibe — all india bar examination",): k="examination"
    else: k="degree"
    if k=="degree" or k=="diploma":
        if re.match(r"(ph\.?d|postdoc)",n): lvl="doctoral"
        elif "postgraduate" in h or re.match(r"(m\.|m[a-z]{1,3}\b|master|llm|ll\.m)",n): lvl="postgraduate"
        elif "undergraduate" in h or "degrees" in h or re.match(r"(b\.|b[a-z]{1,4}\b|bachelor)",n): lvl="undergraduate"
        else: lvl="unspecified"
        if k=="diploma": lvl="diploma"
    else: lvl="unspecified"
    return k,lvl
import os
norm=lambda x: re.sub(r"[^a-z0-9]","",x.lower())
def _abbr(d):
    m_=re.search(r"\(([^()]*)\)\s*$",d); return norm(m_.group(1)) if m_ else norm(d)
UGC_ROWS=list(csv.DictReader(open('qualifications.csv',encoding='utf-8')))
UGC_KEYS={}
for r_ in UGC_ROWS: UGC_KEYS[_abbr(r_['degree'])]=r_['slug']; UGC_KEYS[norm(r_['degree'])]=r_['slug']
STREAM_FOR_UGC={}
EXISTING={r['slug'] for r in csv.DictReader(open('qualifications.csv',encoding='utf-8'))}
rows,seen=[],{}
sec=None; head=""
for line in open("pathways_brief.md",encoding="utf-8"):
    line=line.rstrip("\n")
    m=re.match(r"## \*\*(\d+)\. (.+?)\*\*",line)
    if m: sec=int(m.group(1)) if int(m.group(1))<=15 else None; head=""; continue
    if line.startswith("# "): sec=None if not line.startswith("# **2") else sec; 
    if line.startswith("# **3.") or line.startswith("# **4"): sec=None
    if sec is None: continue
    h=re.match(r"\*\*(.+?)\*\*\s*$",line)
    if h: head=h.group(1); continue
    b=re.match(r"- (.+)",line)
    if not b: continue
    item=b.group(1).strip()
    if not head or head.lower().startswith(("interdisciplinary",)) and False: continue
    if sec==3 and not head: continue
    body=re.sub(r"\*\*","",item)
    body_body,body_auth=(body.split(":",1)+[""])[:2] if body.endswith(("ICAI","ICSI","ICMAI","CFA Institute","IMA","GARP")) or re.search(r":\s*\S",body) and "—" in body.split(":")[0] else (body,"")
    name=body_body.strip(); auth=body_auth.strip() or None
    if len(name)>120: name=name[:120]
    k,lvl=kind_level(head,name)
    if sec==12 and head.lower()!="degrees": k,lvl="professional_qualification","unspecified"
    if sec==15 and head.lower().startswith("public service"): k,lvl="examination","unspecified"
    if head.lower().startswith("specialist clinical"): k="degree"; continue  # fields of practice, not qualifications
    s=slug(name)
    key=slug(name.split(" — ")[0])
    nk=norm(name.split(" — ")[0])
    if nk in UGC_KEYS or norm(name) in UGC_KEYS:
        STREAM_FOR_UGC.setdefault(UGC_KEYS.get(nk) or UGC_KEYS[norm(name)], STREAMS[sec]); continue
    if not s or key in seen or s in EXISTING: continue
    seen[key]=1
    rows.append(dict(degree=name,slug=s,specialization="",level=lvl,kind=k,stream=STREAMS[sec],awarding_body=auth or "",
                     duration_years="",last_verified="2026-11-26",**SRC))
H=["degree","slug","specialization","level","kind","stream","awarding_body","duration_years","source_url","source_title","source_publisher","source_kind","last_verified"]
csv.DictWriter(open("pathways.csv","w",newline="",encoding="utf-8"),fieldnames=H).writeheader()
with open("pathways.csv","a",newline="",encoding="utf-8") as f: csv.DictWriter(f,fieldnames=H).writerows(rows)
from collections import Counter
print(len(rows),Counter(r["kind"] for r in rows),Counter(r["stream"] for r in rows).most_common(3))

with open("ugc_streams.csv","w",newline="",encoding="utf-8") as f:
    w_=csv.writer(f); w_.writerow(["slug","stream"]); w_.writerows(sorted(STREAM_FOR_UGC.items()))
print(len(STREAM_FOR_UGC),"UGC degrees get a stream from the brief")
