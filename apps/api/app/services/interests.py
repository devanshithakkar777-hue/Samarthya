"""Interest explorer built on Holland's six interest types (the model used by the O*NET Interest Profiler,
https://www.onetcenter.org/IP.html, which is released under CC BY 4.0).

The statements below are original wording written for this platform, not copied from O*NET. It is an
exploration aid, not a psychometric test. The explore terms are suggestions for a reviewer to check.
Answers are scored in memory and never stored.
"""
SOURCE = {"title": "O*NET Interest Profiler (Holland interest types)", "url": "https://www.onetcenter.org/IP.html",
          "publisher": "O*NET Resource Center, US Department of Labor", "checked_on": "2026-11-26"}

TYPES = {
    "R": {"name": "Realistic", "blurb": "You like practical, hands-on work with tools, machines, materials or the outdoors.",
          "terms": ["engineering", "manufacturing", "agriculture", "construction", "technician", "energy"]},
    "I": {"name": "Investigative", "blurb": "You like figuring things out: research, analysis, science, data and solving puzzles.",
          "terms": ["research", "data", "science", "healthcare", "technology", "analytics"]},
    "A": {"name": "Artistic", "blurb": "You like creating and expressing ideas through design, writing, media, performance or music.",
          "terms": ["design", "media", "creative", "architecture", "content", "film"]},
    "S": {"name": "Social", "blurb": "You like helping, teaching, advising and working with people.",
          "terms": ["education", "healthcare", "social work", "counselling", "community", "human resources"]},
    "E": {"name": "Enterprising", "blurb": "You like leading, persuading, starting things and taking business risks.",
          "terms": ["business", "sales", "marketing", "entrepreneurship", "management", "law"]},
    "C": {"name": "Conventional", "blurb": "You like order and detail: organising records, numbers, schedules and clear procedures.",
          "terms": ["finance", "accounting", "banking", "administration", "operations", "compliance"]},
}

ITEMS = [  # 6 statements per type, shown in a fixed mixed order
    ("R", "Repair or assemble a machine, bike or appliance"), ("I", "Run a small experiment to test an idea"),
    ("A", "Design a poster, logo or short video"), ("S", "Explain a topic patiently to someone who is struggling"),
    ("E", "Persuade a group to back your plan"), ("C", "Keep accurate records in a spreadsheet"),
    ("R", "Work outdoors on a build, farm or field project"), ("I", "Look for patterns in a large set of numbers"),
    ("A", "Write a story, script or article"), ("S", "Volunteer to support people in your community"),
    ("E", "Start a small business or campaign"), ("C", "Check documents carefully for mistakes"),
    ("R", "Learn how an engine, circuit or tool works by taking it apart"), ("I", "Read research papers to understand a problem deeply"),
    ("A", "Perform, compose or play music"), ("S", "Mentor or coach a junior student"),
    ("E", "Negotiate a deal or sell an idea"), ("C", "Plan a budget and follow it exactly"),
    ("R", "Operate or maintain equipment"), ("I", "Investigate why something fails and find the cause"),
    ("A", "Come up with original ideas for a brand or a product look"), ("S", "Listen to a friend's problem and help them think it through"),
    ("E", "Lead a team to reach a tight goal"), ("C", "Organise files, schedules or inventory so everything is easy to find"),
    ("R", "Build or fix something with wood, metal or electronics"), ("I", "Learn about science, medicine or technology for fun"),
    ("A", "Take photos or edit images to tell a story"), ("S", "Organise an event that brings people together"),
    ("E", "Take a calculated risk to try a new venture"), ("C", "Follow clear rules to get a process exactly right"),
    ("R", "Test how strong or safe a structure or product is"), ("I", "Build a model or simulation to predict what happens"),
    ("A", "Decorate or redesign a space"), ("S", "Teach a skill to a group"),
    ("E", "Speak up and represent a group in front of others"), ("C", "Compare figures across reports and reconcile them"),
]
SCALE = {1: "Strongly dislike", 2: "Dislike", 3: "Not sure", 4: "Like", 5: "Strongly like"}


def items() -> dict:
    return {"items": [{"n": i, "text": t} for i, (_, t) in enumerate(ITEMS)], "scale": SCALE, "source": SOURCE,
            "note": "Rate how much you would like to do each activity, whether or not you have done it. There are no right answers. "
                    "This helps you explore, it does not decide your career."}


def score(answers: list[int]) -> dict:
    if len(answers) != len(ITEMS) or any(a not in SCALE for a in answers):
        raise ValueError(f"Give {len(ITEMS)} answers, each from 1 to 5")
    totals = {k: 0 for k in TYPES}
    for (k, _), a in zip(ITEMS, answers):
        totals[k] += a
    mx = 6 * 5
    ranked = sorted(totals, key=lambda k: (-totals[k], k))
    top = ranked[:3]
    flat = max(totals.values()) - min(totals.values()) < 5
    return {"code": "".join(top), "flat_profile": flat,
            "types": [{"key": k, "name": TYPES[k]["name"], "score": totals[k], "out_of": mx, "blurb": TYPES[k]["blurb"],
                       "explore_terms": TYPES[k]["terms"]} for k in ranked],
            "note": ("Your scores are close together, so you may enjoy a wide mix of work. " if flat else "")
                    + "Treat this as a starting list of things to look into. Interests change, and many careers blend several types.",
            "source": SOURCE}
