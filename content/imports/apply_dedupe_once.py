import csv, sys
from sqlalchemy import select
from app.db import get_db
from app import models as m
from app.services import curation as cur
DUPS="""mbbs-bachelor-of-medicine-and-bachelor-of-surgery bds-bachelor-of-dental-surgery bams-bachelor-of-ayurvedic-medicine-and-surgery bhms-bachelor-of-homoeopathic-medicine-and-surgery bsms-bachelor-of-siddha-medicine-and-surgery bpt-bachelor-of-physiotherapy bot-bachelor-of-occupational-therapy b-pharm-bachelor-of-pharmacy m-pharm-master-of-pharmacy md-doctor-of-medicine ms-master-of-surgery dm-doctorate-of-medicine-super-speciality m-ch-master-of-chirurgiae mds-master-of-dental-surgery b-com-bachelor-of-commerce bba-bachelor-of-business-administration bbm-bachelor-of-business-management msw-master-of-social-work mpa-master-of-public-administration mpt-master-of-physiotherapy b-f-sc-bachelor-of-fisheries-science b-v-sc-a-h-veterinary-science-and-animal-husbandry m-f-sc ll-b-three-year-graduate-entry-law-degree ll-m-master-of-laws b-arch-bachelor-of-architecture bfa-bachelor-of-fine-arts mfa-master-of-fine-arts bpa-bachelor-of-performing-arts b-p-ed-bachelor-of-physical-education m-p-ed bsw-bachelor-of-social-work""".split()
db=next(get_db()); ed=db.scalar(select(m.User).where(m.User.email==sys.argv[1]))
n=0
for s in DUPS:
    o=db.scalar(select(m.Qualification).where(m.Qualification.slug==s))
    if o: cur.delete(db,ed,"qualifications",o.id); n+=1
k=0
for r in csv.DictReader(open("../../content/imports/ugc_streams.csv")):
    o=db.scalar(select(m.Qualification).where(m.Qualification.slug==r["slug"]))
    if o and not o.stream: cur.update(db,ed,"qualifications",o.id,{"stream":r["stream"]}); k+=1
print("deleted",n,"duplicate rows; streams set on",k,"UGC degrees")
