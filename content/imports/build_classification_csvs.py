"""Builds draft-import CSVs from official classifications. Nothing here is invented:
every name comes from the cited source text; descriptions only restate that text.
Run: python build_classification_csvs.py   then import each CSV with `python -m app.cli import ...`"""
import csv, re

VERIFIED = "2026-11-26"
ISIC_URL = "https://unstats.un.org/unsd/classifications/Econ/Download/In%20Text/ISIC_Rev_4_english_structure.txt"
ISIC = dict(source_url=ISIC_URL, source_title="ISIC Rev.4 structure (sections and divisions)",
            source_publisher="United Nations Statistics Division", source_kind="official")
NCO_URL = "https://dge.gov.in/dge/sites/default/files/2022-07/National_Classification_of_Occupations_Vol_I-2015.pdf"
NCO = dict(source_url=NCO_URL, source_title="National Classification of Occupations 2015, Vol. I",
           source_publisher="Directorate General of Employment, Government of India", source_kind="official")
UGC_URL = "https://www.ugc.gov.in/pdfnews/46305564-Degree-Specification.pdf"
UGC = dict(source_url=UGC_URL, source_title="Degrees specified under Section 22 of the UGC Act (consolidated list)",
           source_publisher="University Grants Commission", source_kind="official")
UGC22_URL = "https://nift.ac.in/sites/default/files/2025-06/UGC%20Gazette%2003.03.2022.pdf"
UGC22 = dict(source_url=UGC22_URL, source_title="UGC Gazette notification, 3 March 2022 (specified degrees)",
             source_publisher="University Grants Commission", source_kind="official")

def slug(s, n=70):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-")

SECTIONS = {
"A":"Agriculture, forestry and fishing","B":"Mining and quarrying","C":"Manufacturing",
"D":"Electricity, gas, steam and air conditioning supply","E":"Water supply; sewerage, waste management and remediation activities",
"F":"Construction","G":"Wholesale and retail trade; repair of motor vehicles and motorcycles","H":"Transportation and storage",
"I":"Accommodation and food service activities","J":"Information and communication","K":"Financial and insurance activities",
"L":"Real estate activities","M":"Professional, scientific and technical activities","N":"Administrative and support service activities",
"O":"Public administration and defence; compulsory social security","P":"Education","Q":"Human health and social work activities",
"R":"Arts, entertainment and recreation","S":"Other service activities",
"T":"Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use",
"U":"Activities of extraterritorial organizations and bodies"}
DIV_RANGES = {"A":(1,3),"B":(5,9),"C":(10,33),"D":(35,35),"E":(36,39),"F":(41,43),"G":(45,47),"H":(49,53),"I":(55,56),"J":(58,63),
"K":(64,66),"L":(68,68),"M":(69,75),"N":(77,82),"O":(84,84),"P":(85,85),"Q":(86,88),"R":(90,93),"S":(94,96),"T":(97,98),"U":(99,99)}
DIVS = """01|Crop and animal production, hunting and related service activities
02|Forestry and logging
03|Fishing and aquaculture
05|Mining of coal and lignite
06|Extraction of crude petroleum and natural gas
07|Mining of metal ores
08|Other mining and quarrying
09|Mining support service activities
10|Manufacture of food products
11|Manufacture of beverages
12|Manufacture of tobacco products
13|Manufacture of textiles
14|Manufacture of wearing apparel
15|Manufacture of leather and related products
16|Manufacture of wood and of products of wood and cork, except furniture; manufacture of articles of straw and plaiting materials
17|Manufacture of paper and paper products
18|Printing and reproduction of recorded media
19|Manufacture of coke and refined petroleum products
20|Manufacture of chemicals and chemical products
21|Manufacture of basic pharmaceutical products and pharmaceutical preparations
22|Manufacture of rubber and plastics products
23|Manufacture of other non-metallic mineral products
24|Manufacture of basic metals
25|Manufacture of fabricated metal products, except machinery and equipment
26|Manufacture of computer, electronic and optical products
27|Manufacture of electrical equipment
28|Manufacture of machinery and equipment n.e.c.
29|Manufacture of motor vehicles, trailers and semi-trailers
30|Manufacture of other transport equipment
31|Manufacture of furniture
32|Other manufacturing
33|Repair and installation of machinery and equipment
35|Electricity, gas, steam and air conditioning supply
36|Water collection, treatment and supply
37|Sewerage
38|Waste collection, treatment and disposal activities; materials recovery
39|Remediation activities and other waste management services
41|Construction of buildings
42|Civil engineering
43|Specialized construction activities
45|Wholesale and retail trade and repair of motor vehicles and motorcycles
46|Wholesale trade, except of motor vehicles and motorcycles
47|Retail trade, except of motor vehicles and motorcycles
49|Land transport and transport via pipelines
50|Water transport
51|Air transport
52|Warehousing and support activities for transportation
53|Postal and courier activities
55|Accommodation
56|Food and beverage service activities
58|Publishing activities
59|Motion picture, video and television programme production, sound recording and music publishing activities
60|Programming and broadcasting activities
61|Telecommunications
62|Computer programming, consultancy and related activities
63|Information service activities
64|Financial service activities, except insurance and pension funding
65|Insurance, reinsurance and pension funding, except compulsory social security
66|Activities auxiliary to financial service and insurance activities
68|Real estate activities
69|Legal and accounting activities
70|Activities of head offices; management consultancy activities
71|Architectural and engineering activities; technical testing and analysis
72|Scientific research and development
73|Advertising and market research
74|Other professional, scientific and technical activities
75|Veterinary activities
77|Rental and leasing activities
78|Employment activities
79|Travel agency, tour operator, reservation service and related activities
80|Security and investigation activities
81|Services to buildings and landscape activities
82|Office administrative, office support and other business support activities
84|Public administration and defence; compulsory social security
85|Education
86|Human health activities
87|Residential care activities
88|Social work activities without accommodation
90|Creative, arts and entertainment activities
91|Libraries, archives, museums and other cultural activities
92|Gambling and betting activities
93|Sports activities and amusement and recreation activities
94|Activities of membership organizations
95|Repair of computers and personal and household goods
96|Other personal service activities
97|Activities of households as employers of domestic personnel
98|Undifferentiated goods- and services-producing activities of private households for own use
99|Activities of extraterritorial organizations and bodies"""
divs = [tuple(l.split("|", 1)) for l in DIVS.splitlines()]
assert len(divs) == 88, len(divs)

def w(name, header, rows):
    with open(name, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=header); wr.writeheader(); wr.writerows(rows)

# ---- sectors
HOLD_SLUG = "unplaced-occupation-groups"
sec_rows, sec_slug = [], {}
for L, title in SECTIONS.items():
    lo, hi = DIV_RANGES[L]
    ds = [f"{c} {t}" for c, t in divs if lo <= int(c) <= hi]
    name = title if len(title) <= 120 else "Households as employers and for own use"
    sl = f"isic-{L.lower()}-{slug(name, 60)}"
    sec_slug[L] = sl
    summary = (f"ISIC Rev.4 Section {L}, official title: \"{title}\". Divisions in this section: " + "; ".join(ds) + ".")
    sec_rows.append(dict(name=name, slug=sl, summary=summary, last_verified=VERIFIED, **ISIC))
sec_rows.append(dict(name="Cross-sector occupation groups (placement pending)", slug=HOLD_SLUG,
    summary="Holding area, not an official classification. NCO-2015 occupation groups whose titles do not name one industry sit here until a reviewer places them under the sectors where the work is actually done. Do not publish this sector.",
    last_verified=VERIFIED, **NCO))
H = ["name","slug","summary","source_url","source_title","source_publisher","source_kind","last_verified"]
w("sectors.csv", H, sec_rows)

# ---- roles (NCO-2015 groups)
NCO_TXT = """1|Managers
11|Chief Executives, Senior Officials and Legislators
111|Legislators and Senior Officials
112|Managing Directors and Chief Executives
12|Administrative and Commercial Managers
121|Business Services and Administration Managers
122|Sales, Marketing and Development Managers
13|Production and Specialized Services Managers
131|Production Managers in Agriculture, Forestry and Fisheries
132|Manufacturing, Mining, Construction and Distribution Managers
133|Information and Communications Technology Services Manager
134|Professional Services Managers
14|Hospitality, Retail and Other Services Managers
141|Hotel and Restaurant Managers
142|Retail and Wholesale Trade Managers
143|Other Services Managers
2|Professionals
21|Science and Engineering Professionals
211|Physical and Earth Science Professionals
212|Mathematicians, Actuaries and Statisticians
213|Life Sciences Professionals
214|Engineering Professionals (Excluding Electrotechnology)
215|Electrotechnology Engineers
216|Architects, Planners, Surveyors and Designers
22|Health Professionals
221|Medical Doctors
222|Nursing and Midwifery Professionals
223|Traditional and Complementary Medicine Professionals
224|Paramedical Practitioners
225|Veterinarians
226|Other Health Professionals
23|Teaching Professionals
231|University and Higher Education Teachers
232|Vocational Education Teachers
233|Secondary Education Teachers
234|Primary School and Early Childhood Teachers
235|Other Teaching Professionals
24|Business and Administrative Professionals
241|Finance Professionals
242|Administration Professionals
243|Sales, Marketing and Public Relations Professionals
25|Information and Communication Technology Professionals
251|Software and Application Developers, and Analysts
252|Database and Network Professionals
26|Legal, Social and Cultural Professionals
261|Legal Professionals
262|Librarians, Archivists and Curators
263|Social and Religious Professionals
264|Authors, Journalists and Linguists
265|Creative and Performing Artists
31|Science and Engineering Associate Professionals
311|Physical and Engineering Science Technicians
312|Mining, Manufacturing and Construction Supervisors
313|Process Control Technicians
314|Life Science Technicians and Related Associate Professionals
315|Ship and Aircraft Controllers, and Technicians
32|Health Associate Professionals
321|Medical and Pharmaceutical Technicians
322|Nursing and Midwifery Associate Professionals
323|Traditional and Complementary Medicine Associate Professionals
324|Veterinary Technicians and Assistants
325|Other Health Associate Professionals
33|Business and Administration Associate Professionals
331|Financial and Mathematical Associate Professionals
332|Sales and Purchasing Agents and Brokers
333|Business Service Agents
334|Administrative and Specialized Secretaries
335|Government Regulatory Associate Professionals
34|Legal, Social, Cultural and Related Associate Professionals
341|Legal, Social and Religious Associate Professionals
342|Sports and Fitness Workers
343|Administrative Associate Professionals
35|Information and Communications Technicians
351|Information and Communication Technology Operations and User Support Technicians
352|Telecommunication and Broadcasting Technicians
41|General and Keyboard Clerks
411|General Office Clerks
412|Secretaries (General)
413|Keyboard Operators
42|Customer Services Clerks
421|Tellers, Money Collectors and Related Clerks
422|Client Information Workers
43|Numerical and Material Recording Clerks
431|Numerical Clerks
432|Material Recording and Transport Clerks
44|Other Clerical Support Workers
441|Other Clerical Support Workers
51|Personal Service Workers
511|Travel Attendants, Conductors and Guides
512|Cooks
513|Waiters and Bartenders
514|Hairdressers, Beauticians and Related Workers
515|Building and Housekeeping Supervisors
516|Other Personal Services Workers
52|Sales Workers
521|Street and Market Salespersons
522|Shop Salespersons
523|Cashiers and Ticket Clerks
524|Other Sales Workers
53|Personal Care Workers
531|Child Care Workers and Teachers' Aides
532|Personal Care Workers in Health Services
54|Protective Service Workers
541|Protective Service Workers
61|Market-Oriented Skilled Agricultural Workers
611|Market Gardeners & Crop Growers
612|Animal Producers
613|Mixed Crop and Animal Workers
62|Market-Oriented Skilled Forestry, Fishery and Hunting Workers
621|Forestry and Related Workers
622|Fishery Workers, Hunters and Trappers
63|Subsistence Farmers, Fishers, Hunters and Gatherers
631|Subsistence Crop Farmers
632|Subsistence Livestock Farmers
633|Subsistence Mixed Crop and Livestock Farmers
634|Subsistence Fishers, Hunters, Trappers and Gatherers
71|Building and Related Trade Workers (Excluding Electricians)
711|Building Frames and Related Trades Workers
712|Building Finishers and Related Trades Workers
713|Painters, Builders, Structure Cleaners and Related Trades Workers
72|Metal, Machinery and Related Trades Workers
721|Sheet and Structural Metal Workers, Moulders and Welders, and Related Workers
722|Blacksmiths, Tool Makers and Related Trades Workers
723|Machinery Mechanics and Repairers
73|Handicraft and Printing Workers
731|Handicraft Workers
732|Printing Trades Workers
74|Electrical and Electronics Trades Workers
741|Electrical Equipment Installers and Repairers
742|Electronics and Telecommunication Installers and Repairers
75|Food Processing, Woodworking, Garment and Other Craft and Related Trades Workers
751|Food Processing and Related Trade Workers
752|Wood Treaters, Cabinet Makers and Related Trades Workers
753|Garment and Related Trades Workers
754|Other Craft and Related Workers
81|Stationary Plant and Machine Operators
811|Mining and Mineral Processing Plant Operators
812|Metal Processing and Finishing Plant Operators
813|Chemical and Photographic Products Plant and Machine Operators
814|Rubber, Plastic and Paper Products Machine Operators
815|Textile, Fur and Leather Products Machine Operators
816|Food and Related Products Machine Operators
817|Wood Processing and Papermaking Plant Operators
818|Other Stationary Plant and Machine Operators
82|Assemblers
821|Assemblers
83|Drivers and Mobile Plant Operators
831|Locomotive Engine Drivers and Related Workers
832|Car, Van and Motorcycle Drivers
833|Heavy Truck and Bus Drivers
834|Mobile Plant Operators
835|Ships' Deck Crews and Related Workers
8|Plant and Machine Operators, and Assemblers
9|Elementary Occupations
91|Cleaners and Helpers
911|Domestic, Hotel and Office Cleaners and Helpers
912|Vehicle, Window, Laundry and Other Hand Cleaners
92|Agricultural, Forestry and Fishery Labourers
921|Agricultural, Forestry and Fishery Labourers
93|Labourers in Mining, Construction, Manufacturing and Transport
931|Mining and Construction Labourers
932|Manufacturing Labourers
933|Transport and Storage Labourers
94|Food Preparation Assistants
941|Food Preparation Assistants
95|Street and Related Sales and Services Workers
951|Street and Related Service Workers
952|Street Vendors (Excluding Food)
96|Refuse Workers and Other Elementary Workers
961|Refuse Workers
962|Other Elementary Workers"""
nco = {c: t for c, t in (l.split("|", 1) for l in NCO_TXT.splitlines())}
# Major groups 3..7 titles are not in the fetched text; their groups are still listed under their sub-divisions.
MAJOR = {"1": nco["1"], "2": nco["2"], "8": nco["8"], "9": nco["9"]}
# Placement only where the group title itself names the field. Everything else is left for a reviewer.
PLACE = {"131":"A","133":"J","141":"I","142":"G","221":"Q","222":"Q","223":"Q","224":"Q","226":"Q","225":"M",
 "231":"P","232":"P","233":"P","234":"P","235":"P","251":"J","252":"J","262":"R","265":"R","315":"H","322":"Q","323":"Q",
 "324":"M","325":"Q","342":"R","351":"J","352":"J","512":"I","513":"I","514":"S","532":"Q","611":"A","612":"A","613":"A",
 "621":"A","622":"A","631":"A","632":"A","633":"A","634":"A","711":"F","712":"F","713":"F","732":"C","751":"C","752":"C",
 "753":"C","811":"B","831":"H","832":"H","833":"H","835":"H","921":"A"}
rows = []
for code, title in nco.items():
    if len(code) != 3: continue
    sub = nco[code[:2]]
    major = nco.get(code[0]) or "major group not captured"
    L = PLACE.get(code)
    desc = (f"NCO-2015 occupation group {code}, in sub-division {code[:2]} \"{sub}\""
            + (f" (major group {code[0]} \"{major}\")" if code[0] in MAJOR else "") + ". "
            "Group-level entry taken from the classification. Individual occupations, entry requirements and typical employers have not been added or reviewed. ")
    desc += (f"Placed under ISIC section {L} because the group title names that field; reviewer to confirm." if L
             else "Sector placement pending: the group title does not name a single industry.")
    rows.append(dict(title=title, slug=f"nco-{code}-{slug(title, 60)}", sector_slug=sec_slug[L] if L else HOLD_SLUG,
                     job_family=sub[:120], level="unspecified", description=desc, last_verified=VERIFIED, **NCO))
H = ["title","slug","sector_slug","job_family","level","description","source_url","source_title","source_publisher","source_kind","last_verified"]
w("roles.csv", H, rows)

# ---- qualifications
UGC_TXT = open("ugc_consolidated.txt", encoding="utf-8").read().strip().splitlines()
qrows, seen = [], set()
def level(name):
    n = name.lower()
    if n.startswith("bachelor"): return "undergraduate"
    if n.startswith("master"): return "postgraduate"
    if name in ("Doctor of Philosophy", "Doctor of Science", "Doctor of Literature", "Doctor of Laws", "Doctor of Law", "Doctor of Engineering", "Doctor of Music", "Doctor of Education"): return "doctoral"
    return "unspecified"
GAZ22 = {"MCA":("Master of Computer Applications",2),"B.F.Tech.":("Bachelor of Fashion Technology",4),"M.F.Tech.":("Master of Fashion Technology",2),
 "M.F.M.":("Master of Fashion Management",2),"B.U.D.":("Bachelor of Urban Design",4),"M.U.D.":("Master of Urban Design",2),
 "B.S.M.":("Bachelor of Sports Management",3),"M.S.M.":("Masters of Sports Management",2),"B.S.S.":("Bachelor of Sports Science",3),
 "M.S.S.":("Master of Sports Science",2),"BOT":("Bachelor of Occupational Therapy",None)}
for abbr, (name, yrs) in GAZ22.items():
    qrows.append(dict(degree=f"{name} ({abbr})", slug=slug(abbr), level=level(name), kind="degree", duration_years=yrs if yrs else "",
                      last_verified=VERIFIED, **UGC22)); seen.add(slug(abbr))
for line in UGC_TXT:
    no, abbr, name = [x.strip() for x in line.split("|")][:3]
    sl = slug(abbr)
    if sl in seen:  # slug clash: disambiguate by serial number from the source
        sl = f"{sl}-{no}"
    if slug(abbr) in {slug(a) for a in GAZ22} : continue
    seen.add(sl)
    label = name if abbr.lower() == name.lower() else f"{name} ({abbr})"
    qrows.append(dict(degree=label[:120], slug=sl, level=level(name), kind="degree", duration_years="", last_verified=VERIFIED, **UGC))
H = ["degree","slug","level","kind","duration_years","source_url","source_title","source_publisher","source_kind","last_verified"]
w("qualifications.csv", H, qrows)
print(len(sec_rows), "sectors;", len(rows), "roles;", len(qrows), "qualifications")
