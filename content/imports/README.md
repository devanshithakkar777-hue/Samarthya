# Classification imports (drafts only)

Built by `build_classification_csvs.py` from official sources read on 2026-11-26.
Import order: sectors, qualifications, roles. Everything lands as a **draft**; nothing is public until a different reviewer approves it.

| File | Rows | Source |
|---|---|---|
| sectors.csv | 21 ISIC Rev.4 sections + 1 holding sector | UN Statistics Division, ISIC Rev.4 structure |
| roles.csv | 127 NCO-2015 occupation groups (3-digit) | DGE, National Classification of Occupations 2015 Vol. I |
| qualifications.csv | 151 degrees | UGC consolidated specified-degree list (142) + UGC Gazette 3 Mar 2022 (9 new, plus MCA and BOT updates) |

Known limits: the roles are groups, not individual jobs (no requirements, employers or degrees linked); 74 groups sit in the holding sector until a reviewer places them; 141 degrees have no stated duration (left blank on purpose); BOT's 4½ years does not fit the integer column and is left blank; the UGC list is not exhaustive of newer 4-year honours or professional courses (CA, CS, etc.).

```
python -m app.cli import sectors ../../content/imports/sectors.csv --as <editor email>
python -m app.cli import qualifications ../../content/imports/qualifications.csv --as <editor email>
python -m app.cli import roles ../../content/imports/roles.csv --as <editor email>
```

## pathways.csv (from the Education & Qualification Directory brief)

493 rows built by `build_pathways_csv.py` from `pathways_brief.md` (the project team's reviewed brief). Each row has a type (degree, diploma, certificate, professional qualification, certification, examination), one of 15 primary streams, and an awarding body where the brief names one. Import after `qualifications.csv`. Still drafts: eligibility, duration, recognition, fees and official links from the brief's 15-field template are not in the brief's lists and still need filling per entry. The source URL is a placeholder for the brief; replace it with a real hosted link if you publish it. `pathways_tables.csv` (78 rows, `build_pathways_tables_csv.py`) adds the brief's section 4 (professional qualifications by domain) and section 16 (specialist fields, used as extra stream values). Vague entries such as "defence-related degrees" were skipped, not guessed; the "Healthcare" domain row is skipped because it names no concrete qualification.

## Education & Qualification Explorer

Public pages `/pathways` (stage, stream, type filters and search) and `/pathways/<slug>` (what is known, what is "not yet verified", sectors and roles it leads to). API: `GET /v1/pathways`, `GET /v1/pathways/{slug}`. Only published qualifications appear. The stage chips are starting filters, not eligibility checks. Empty fields show "Not yet verified" instead of a guess.

## enrich_professional.csv (official-source detail for CA, CS, CMA India, CFA)

Adds eligibility, entry route, training, recognition (where an official page states it), cost and official link to four existing qualifications, each sourced to the awarding body's own page (ICAI, ICSI, ICMAI, CFA Institute), read 2026-11-26. Apply with `python -m app.cli enrich qualifications ../../content/imports/enrich_professional.csv --as <editor email>` after importing pathways.csv. The row's source is replaced by the official page; extra pages are cited inline in the text. Not covered: syllabus, further education, alternative pathways, ICAI recognition wording, ICSI fees, CA and CMA durations. Re-check these pages before approving; requirements change each exam cycle.

## Duplicate clean-up (2026-11-26)

The first pathways import duplicated 32 degrees already in the UGC list (for example MBBS and B.Pharm). `build_pathways_csv.py` now skips any row whose abbreviation matches a UGC degree and writes `ugc_streams.csv`, which gives those 39 UGC degrees the stream from the brief. Databases loaded earlier can run `apply_dedupe_once.py <editor email>` (with `PYTHONPATH=apps/api`) to delete the 32 draft duplicates and set the streams; published rows must be unpublished first.

## enrich_councils.csv (statutory councils)

Eligibility, entry route, training, recognition and duration for MBBS (National Medical Commission), B.Arch (Council of Architecture), B.Pharm, Pharm.D and D.Pharm (Pharmacy Council of India) and LL.B. (Bar Council of India), from each council's own pages, read 2026-11-26. Gaps stated plainly in the text: B.Arch exact marks (the CoA notice is linked, not summarised), Pharm.D's full subject list, D.Pharm eligibility, MBBS duration (4½ years plus internship does not fit a whole-number field), LL.B. duration (3 or 5 years). Apply with `python -m app.cli enrich qualifications ../../content/imports/enrich_councils.csv --as <editor email>`.
