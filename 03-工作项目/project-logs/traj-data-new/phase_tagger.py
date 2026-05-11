"""Heuristic phase tagging and drift/marker detection for v2 trajectories.

Works with structured action objects: {"tool_name": "Read", "args": {...}}
instead of v1 flat action strings like 'Read(file_path="/a.py")'.
"""
from __future__ import annotations

PHASE_NAMES = {
    "localization": ("Localization", "问题定位"),
    "editing": ("Editing", "补丁生成"),
    "verification": ("Verification", "验证与测试"),
    "submission": ("Submission", "提交"),
}

LOCALIZATION_TOOLS = {"Read", "Glob", "Grep", "LSP", "Agent"}
EDITING_TOOLS = {"Write", "Edit", "NotebookEdit"}
VERIFICATION_PATTERNS = ["pytest", "test"]
SUBMISSION_PATTERNS = ["git commit", "git push"]


def classify_action_v2(step: dict) -> str:
    """Classify a step dict by its action.tool_name."""
    action = step["action"]
    tool_name = action["tool_name"]

    if tool_name == "respond_to_user":
        return "inherited"

    if tool_name in LOCALIZATION_TOOLS:
        return "localization"

    if tool_name in EDITING_TOOLS:
        return "editing"

    if tool_name == "Bash":
        cmd = action.get("args", {}).get("command", "").lower()

        for pattern in SUBMISSION_PATTERNS:
            if pattern in cmd:
                return "submission"

        for pattern in VERIFICATION_PATTERNS:
            if pattern in cmd:
                return "verification"

        return "editing"

    return "editing"


def tag_phases_v2(steps: list[dict]) -> list[dict]:
    """Group consecutive same-phase steps into phase boundary dicts."""
    if not steps:
        return []

    labels = [classify_action_v2(step) for step in steps]

    # Resolve inherited labels
    for i, label in enumerate(labels):
        if label == "inherited":
            labels[i] = labels[i - 1] if i > 0 else "editing"

    phases = []
    current_label = labels[0]
    start_step = steps[0]["step_id"]

    for i in range(1, len(labels)):
        if labels[i] != current_label:
            en, zh = PHASE_NAMES.get(current_label, (current_label.title(), current_label))
            phases.append({
                "name": en,
                "name_zh": zh,
                "start_step": start_step,
                "end_step": steps[i - 1]["step_id"],
                "label": current_label,
            })
            current_label = labels[i]
            start_step = steps[i]["step_id"]

    en, zh = PHASE_NAMES.get(current_label, (current_label.title(), current_label))
    phases.append({
        "name": en,
        "name_zh": zh,
        "start_step": start_step,
        "end_step": steps[-1]["step_id"],
        "label": current_label,
    })

    return phases


def detect_markers_v2(steps: list[dict]) -> list[dict]:
    """Detect drift-start, search-loop, churn, and milestone markers."""
    markers = []
    n = len(steps)

    if n == 0:
        return markers

    # Milestone markers
    markers.append({"step": steps[0]["step_id"], "type": "milestone", "reason": "Session start"})
    if n > 1:
        markers.append({"step": steps[-1]["step_id"], "type": "milestone", "reason": "Session end"})

    labels = [classify_action_v2(step) for step in steps]
    for i, label in enumerate(labels):
        if label == "inherited":
            labels[i] = labels[i - 1] if i > 0 else "editing"

    # Drift detection: 4+ consecutive edits without verification
    consecutive_edit = 0
    drift_marked = False
    for i, label in enumerate(labels):
        if label == "editing":
            consecutive_edit += 1
            if consecutive_edit >= 4 and not drift_marked:
                markers.append({
                    "step": steps[i]["step_id"],
                    "type": "drift-start",
                    "reason": f"{consecutive_edit} consecutive edits without verification",
                })
                drift_marked = True
        elif label == "verification":
            consecutive_edit = 0
            drift_marked = False
        else:
            consecutive_edit = 0
            drift_marked = False

    # Search-loop detection: 4+ consecutive localizations
    consecutive_search = 0
    search_marked = False
    for i, label in enumerate(labels):
        if label == "localization":
            consecutive_search += 1
            if consecutive_search >= 4 and not search_marked:
                markers.append({
                    "step": steps[i]["step_id"],
                    "type": "search-loop",
                    "reason": "Extended search without editing — possible localization failure",
                })
                search_marked = True
        else:
            consecutive_search = 0
            search_marked = False

    # Churn detection: 3+ edits to same file in 5-step window
    churn_files: set[str] = set()
    for i in range(n):
        window = steps[max(0, i - 4):i + 1]
        file_edits: dict[str, int] = {}
        for step in window:
            action = step["action"]
            tool_name = action["tool_name"]
            if tool_name in ("Edit", "Write"):
                fp = action.get("args", {}).get("file_path")
                if fp:
                    file_edits[fp] = file_edits.get(fp, 0) + 1

        for fp, count in file_edits.items():
            if count >= 3 and fp not in churn_files:
                churn_files.add(fp)
                markers.append({
                    "step": steps[i]["step_id"],
                    "type": "churn",
                    "reason": f"Repeated edits to {fp} — possible edit recovery failure",
                })

    markers.sort(key=lambda m: (m["step"], m["type"]))

    return markers
