"""FastAPI backend for traj-gep visualization.

Serves the genes.json artifacts from `traj-gep/output/{wzp,zzj}/` and the
static frontend.

    uvicorn backend.main:app --port 8765 --reload
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

VIZ_DIR = Path(__file__).resolve().parent.parent
TRAJ_GEP_DIR = VIZ_DIR.parent
FRONTEND_DIR = VIZ_DIR / "frontend"

GENES_PATHS = {
    "wzp": TRAJ_GEP_DIR / "output" / "wzp" / "genes.json",
    "zzj": TRAJ_GEP_DIR / "output" / "zzj" / "genes.json",
}

PROJECT_LABELS = {
    "wzp": "脑力大冒险",
    "zzj": "超时空要塞",
}


def _load_genes(project: str) -> list[dict]:
    path = GENES_PATHS.get(project)
    if not path or not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _enrich(gene: dict, project: str) -> dict:
    g = dict(gene)
    g["project"] = project
    parts = gene["id"].split("_")
    fam_token = parts[3] if len(parts) >= 4 else "unknown"
    g["family"] = {
        "f1sig": "F1·SIG",
        "f2flow": "F2·FLOW",
        "f3phase": "F3·PHASE",
    }.get(fam_token, fam_token)
    g["family_token"] = fam_token
    return g


app = FastAPI(title="traj-gep · specimen archive")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/genes")
def all_genes() -> dict:
    out: list[dict] = []
    for project in GENES_PATHS:
        for g in _load_genes(project):
            out.append(_enrich(g, project))
    return {"count": len(out), "genes": out}


@app.get("/api/genes/{project}")
def genes_for(project: str) -> dict:
    if project not in GENES_PATHS:
        raise HTTPException(404, "unknown project")
    items = [_enrich(g, project) for g in _load_genes(project)]
    return {"count": len(items), "genes": items}


@app.get("/api/stats")
def stats() -> dict:
    by_project: dict = {}
    overall_genes = 0
    overall_evidence = 0
    overall_categories: Counter = Counter()
    overall_families: Counter = Counter()
    overall_signals: Counter = Counter()

    for project in GENES_PATHS:
        genes = _load_genes(project)
        cats: Counter = Counter(g.get("category", "unknown") for g in genes)
        fams: Counter = Counter(_enrich(g, project)["family"] for g in genes)
        sigs: Counter = Counter()
        sessions: set[str] = set()
        evidence = 0
        for g in genes:
            for s in g.get("signals_match", []):
                sigs[s] += 1
                overall_signals[s] += 1
            prov = g.get("_provenance", {})
            sessions.update(prov.get("session_hashes_sample", []))
            evidence += prov.get("frequency", 0)
        by_project[project] = {
            "label": PROJECT_LABELS[project],
            "genes": len(genes),
            "by_category": dict(cats),
            "by_family": dict(fams),
            "top_signals": sigs.most_common(20),
            "unique_sessions_sampled": len(sessions),
            "total_evidence_occurrences": evidence,
        }
        overall_genes += len(genes)
        overall_evidence += evidence
        overall_categories.update(cats)
        overall_families.update(fams)

    return {
        "by_project": by_project,
        "overall": {
            "genes": overall_genes,
            "evidence_occurrences": overall_evidence,
            "by_category": dict(overall_categories),
            "by_family": dict(overall_families),
            "top_signals": overall_signals.most_common(20),
        },
    }


# ---------------------------------------------------------------- static


if FRONTEND_DIR.exists():

    @app.get("/")
    def root_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="frontend-static",
    )
