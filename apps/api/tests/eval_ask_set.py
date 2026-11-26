"""The Ask evaluation set: 50 questions with expected outcomes, run on every change.

The knowledge base here is fake, built only for this test. Each case says whether Ask must answer
(and which page it must cite and a phrase the answer must contain) or must refuse. Answerable
cases check the *behaviour* (right page, only sourced text). Replace or extend with real student
questions as they are collected: the admin "unanswered questions" list is the source for them.
"""

# (question, expected_path_or_None, phrase_that_must_appear_or_None)
CASES = [
    # --- requirements ---
    ("What does a Quillmaker need?", "/roles/quillmaker", "Required"),
    ("What skills do I need to become a Quillmaker", "/roles/quillmaker", "Required"),
    ("Requirements for Quillmaker", "/roles/quillmaker", "Required"),
    ("how do I prepare for a Zorbwright role", "/roles/zorbwright", "Required"),
    ("What are the requirements to be a Zorbwright?", "/roles/zorbwright", "Required"),
    ("skills needed for Brindle Analyst", "/roles/brindle-analyst", "Required"),
    ("what is required for a Brindle Analyst job", "/roles/brindle-analyst", "Required"),
    ("Do I need an internship to be a Quillmaker?", "/roles/quillmaker", "internship"),
    ("what should I prepare for Flumox Technician", "/roles/flumox-technician", "Required"),
    ("eligibility for Flumox Technician", "/roles/flumox-technician", "Required"),
    # --- degrees ---
    ("Which degree leads to Quillmaker?", "/roles/quillmaker", "Test Degree A"),
    ("What should I study to become a Zorbwright", "/roles/zorbwright", "Test Degree B"),
    ("qualification for Brindle Analyst", "/roles/brindle-analyst", "Test Degree A"),
    ("Which courses lead to Flumox Technician?", "/roles/flumox-technician", "Test Degree B"),
    ("what background do I need for Quillmaker", "/roles/quillmaker", "Test Degree A"),
    # --- hiring ---
    ("Where can I apply for Quillmaker jobs?", "/roles/quillmaker", "Official hiring pages"),
    ("Who is hiring Zorbwright?", "/roles/zorbwright", "Official hiring pages"),
    ("Which employers hire a Brindle Analyst", "/roles/brindle-analyst", "Official hiring pages"),
    ("careers page for Quillmaker", "/roles/quillmaker", "Official hiring pages"),
    # --- role / sector / skill / company overviews ---
    ("What does a Quillmaker do?", "/roles/quillmaker", "Fake role"),
    ("Tell me about the Zorbwright role", "/roles/zorbwright", "Fake role"),
    ("What is a Brindle Analyst?", "/roles/brindle-analyst", "Fake role"),
    ("Tell me about the Glimmerwork sector", "/explore/glimmerwork", "Fake sector"),
    ("What is the Nimbleforge sector about", "/explore/nimbleforge", "Fake sector"),
    ("What is Frobnication?", "/skills/frobnication", "fake skill"),
    ("Explain the Frobnication skill", "/skills/frobnication", "fake skill"),
    ("How can I learn Frobnication?", "/skills/frobnication", "Ways to learn"),
    ("free resources for Frobnication", "/skills/frobnication", "free"),
    ("Tell me about Wibblesworth Industries", "/companies/wibblesworth", "Fake company"),
    ("What does Wibblesworth do?", "/companies/wibblesworth", "Fake company"),
    ("Who is Pondercorp", "/companies/pondercorp", "Fake company"),
    # --- must refuse: outside the knowledge base ---
    ("Who won the cricket match yesterday?", None, None),
    ("What is the capital of France?", None, None),
    ("How do I bake sourdough bread?", None, None),
    ("Tell me about Dragonfruit Cultivation careers", None, None),
    ("What does a Plumbus Engineer need?", None, None),
    ("Which degree leads to Astronaut?", None, None),
    ("Where can I apply for Lion Tamer jobs?", None, None),
    ("What is quantum chromodynamics?", None, None),
    ("Explain the Gloopification skill", None, None),
    ("Tell me about Megacorp Unlimited", None, None),
    ("Best phone under 15000", None, None),
    ("Is it going to rain tomorrow?", None, None),
    ("Tell me a joke", None, None),
    ("How do I get a visa for Canada?", None, None),
    # --- must refuse: predictions and guarantees ---
    ("Will I get a job as a Quillmaker?", None, None),
    ("How much will a Zorbwright earn?", None, None),
    ("What is the salary of a Brindle Analyst", None, None),
    ("Can you guarantee I will get placed?", None, None),
    ("What are my chances of becoming a Flumox Technician?", None, None),
]
assert len(CASES) == 50, len(CASES)
