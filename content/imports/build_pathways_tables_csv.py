"""Imports the two tables of the brief: section 4 (professional qualifications by domain) and section 16 (specialist fields).
Rows already in qualifications.csv / pathways.csv are skipped. Vague entries (no concrete name) are skipped, not guessed."""
import csv, re
SRC = dict(source_url="https://samarthya.example/briefs/education-pathways-directory",
           source_title="Samarthya Education and Qualification Directory brief (reviewed by the project team)",
           source_publisher="Samarthya project team", source_kind="third_party")
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:80].strip("-")
FIN,MGT,TECH,EDU="Finance, Banking and Economics","Management and Business","Engineering and Technology","Education, Public Policy and Public Service"
D4={"Accounting":(FIN,"professional_qualification"),"Corporate governance":(FIN,"professional_qualification"),
 "Investment management":(FIN,"professional_qualification"),"Risk management":(FIN,"professional_qualification"),
 "Actuarial science":(FIN,"examination"),"Financial planning":(FIN,"professional_qualification"),
 "Internal audit":(FIN,"professional_qualification"),"IT audit":(FIN,"professional_qualification"),
 "Securities markets":(FIN,"certification"),"Taxation":(FIN,"professional_qualification"),
 "Project management":(MGT,"certification"),"Human resources":(MGT,"certification"),"Supply chain":(MGT,"certification"),
 "Quality management":(MGT,"certification"),"Cybersecurity":(TECH,"certification"),"Cloud computing":(TECH,"certification"),
 "Networking":(TECH,"certification"),"Software and DevOps":(TECH,"certification"),
 "Architecture and construction":("Architecture, Planning and Design","certification"),
 "Law":("Law","examination"),"Education":(EDU,"examination"),"Languages":("Humanities and Arts","certification"),
 "Aviation":("Aviation","licence")}
GENERIC=re.compile(r"(related|qualifications|programmes|licensing|certificates|registration|pathways|degrees|examination pathways|practitioner)",re.I)
rows,seen=[],{r["slug"] for f in ("qualifications.csv","pathways.csv") for r in csv.DictReader(open(f,encoding="utf-8"))}
def add(name,stream,kind,level="unspecified"):
    name=name.strip().strip(".")
    s=slug(name)
    if not s or s in seen or any(x.startswith(s+'-') for x in seen) or GENERIC.search(name) or len(name)>120: return
    seen.add(s)
    rows.append(dict(degree=name,slug=s,specialization="",level=level,kind=kind,stream=stream,awarding_body="",duration_years="",
                     last_verified="2026-11-26",**SRC))
sec=None
for line in open("pathways_brief.md",encoding="utf-8"):
    if line.startswith("# **4."): sec=4; continue
    if line.startswith("## **16."): sec=16; continue
    if line.startswith("# **") and not line.startswith(("# **4.","# **16.")): sec=None if sec else sec
    if line.startswith("# **5.") or line.startswith("# **3."): sec=None
    if sec and line.startswith("|") and not re.match(r"\|\s*-",line):
        cells=[c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells)<2 or cells[0] in ("Domain","Specialist field") : continue
        if sec==4 and cells[0] in D4:
            st,k=D4[cells[0]]
            for n in cells[1].split(","): 
                n=n.strip()
                add(n, st, "examination" if n.startswith(("AIBE","CTET","State TET","UGC-NET","JRF","IELTS","TOEFL")) else "licence" if n in("CPL","ATPL") else k)
        if sec==16:
            field=cells[0]
            for n in re.split(r",\s*(?![^()]*\))",cells[1]):
                n=n.strip()
                if re.match(r"(NDA|CDS|AFCAT)$",n): k="examination"
                elif n.startswith("Diploma"): k="diploma"
                elif n in ("CPL","Commercial Pilot Licence") or "Licence" in n: k="licence"
                elif n.startswith(("DNS","GP Rating")): k="certificate"
                else: k="degree"
                add(n,field,k)
H=["degree","slug","specialization","level","kind","stream","awarding_body","duration_years","source_url","source_title","source_publisher","source_kind","last_verified"]
with open("pathways_tables.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=H); w.writeheader(); w.writerows(rows)
print(len(rows)); print([r["degree"] for r in rows][:60])
