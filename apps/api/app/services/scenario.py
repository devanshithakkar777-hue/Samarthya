"""Branching scenarios: validation of the authored graph and the step function.

node:   {"key": str, "text": str, "end": bool, "debrief": str|None,
         "choices": [{"label": str, "next": str, "consequence": str, "scores": {dimension: int}}]}
The first node is the start. A scenario cannot loop, so every run ends.
"""

MAX_NODES = 60


def validate(nodes, dimensions) -> list[str]:
    errs: list[str] = []
    if not isinstance(nodes, list) or not nodes:
        return ["add at least one scene"]
    if len(nodes) > MAX_NODES:
        return [f"too many scenes (limit {MAX_NODES})"]
    dims = set(dimensions or [])
    if not dims:
        errs.append("list the dimensions you score (for example risk, ethics, communication)")
    keys = []
    for i, n in enumerate(nodes):
        if not isinstance(n, dict) or not str(n.get("key", "")).strip() or not str(n.get("text", "")).strip():
            errs.append(f"scene {i + 1} needs a key and text")
            continue
        keys.append(n["key"])
    if len(set(keys)) != len(keys):
        errs.append("scene keys must be unique")
    if errs:
        return errs
    by_key = {n["key"]: n for n in nodes}
    ends = 0
    for n in nodes:
        choices = n.get("choices") or []
        if n.get("end"):
            ends += 1
            if choices:
                errs.append(f"end scene '{n['key']}' must not have choices")
            if not str(n.get("debrief") or "").strip():
                errs.append(f"end scene '{n['key']}' needs a debrief")
            continue
        if len(choices) < 2:
            errs.append(f"scene '{n['key']}' needs at least two choices")
        for c in choices:
            if not str(c.get("label", "")).strip() or not str(c.get("consequence", "")).strip():
                errs.append(f"every choice in '{n['key']}' needs a label and a consequence")
            if c.get("next") not in by_key:
                errs.append(f"a choice in '{n['key']}' leads to a scene that does not exist")
            for d, v in (c.get("scores") or {}).items():
                if d not in dims:
                    errs.append(f"'{d}' is not a listed dimension")
                if not isinstance(v, int) or isinstance(v, bool) or not -3 <= v <= 3:
                    errs.append("scores must be whole numbers from -3 to 3")
    if ends == 0:
        errs.append("add at least one end scene")
    if errs:
        return errs
    # no cycles, everything reachable
    state: dict[str, int] = {}

    def visit(k: str) -> bool:
        if state.get(k) == 1:
            return False
        if state.get(k) == 2:
            return True
        state[k] = 1
        for c in by_key[k].get("choices") or []:
            if not visit(c["next"]):
                return False
        state[k] = 2
        return True

    if not visit(nodes[0]["key"]):
        return ["a choice leads back to an earlier scene; scenarios cannot loop"]
    unreachable = [k for k in by_key if k not in state]
    if unreachable:
        errs.append(f"scenes never reached from the start: {', '.join(unreachable)}")
    return errs


def public_node(n: dict) -> dict:
    """A scene as the student sees it: no scores, no future consequences."""
    return {"key": n["key"], "text": n["text"], "end": bool(n.get("end")), "debrief": n.get("debrief") if n.get("end") else None,
            "choices": [{"index": i, "label": c["label"]} for i, c in enumerate(n.get("choices") or [])]}


def step(nodes: list, current_key: str, choice_index: int) -> tuple[dict, dict, dict]:
    """Returns (chosen choice, score deltas, next scene)."""
    by_key = {n["key"]: n for n in nodes}
    node = by_key[current_key]
    choices = node.get("choices") or []
    if node.get("end") or not 0 <= choice_index < len(choices):
        raise ValueError("invalid choice")
    c = choices[choice_index]
    return c, dict(c.get("scores") or {}), by_key[c["next"]]
