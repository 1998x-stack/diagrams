"""Genes visualization API — serves accumulated gene data from plugin directories."""

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

PLUGIN_SOURCES = {
    "claude-acc": Path(__file__).resolve().parent.parent / "claude-acc" / "plugins",
    "opencode-acc": Path(__file__).resolve().parent.parent / "opencode-acc" / "plugins",
}

app = FastAPI(title="Genes Visualization API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_cache: dict[str, Any] = {"genes": None, "mtimes": {}}


def _collect_mtimes() -> dict[str, float]:
    mtimes = {}
    for source_path in PLUGIN_SOURCES.values():
        if not source_path.exists():
            continue
        for genes_file in source_path.rglob("genes.json"):
            mtimes[str(genes_file)] = genes_file.stat().st_mtime
    return mtimes


def scan_genes() -> list[dict[str, Any]]:
    mtimes = _collect_mtimes()
    if _cache["genes"] is not None and mtimes == _cache["mtimes"]:
        return _cache["genes"]

    genes = []
    for source_name, source_path in PLUGIN_SOURCES.items():
        if not source_path.exists():
            continue
        for genes_file in source_path.rglob("genes.json"):
            category_dir = genes_file.parent.name
            try:
                entries = json.loads(genes_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for entry in entries:
                entry["_source"] = source_name
                entry["_category_dir"] = category_dir
                genes.append(entry)

    _cache["genes"] = genes
    _cache["mtimes"] = mtimes
    return genes


@app.get("/api/genes")
def get_genes():
    genes = scan_genes()
    return {"total": len(genes), "genes": genes}


@app.get("/api/stats")
def get_stats():
    genes = scan_genes()
    by_source: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_source_category: dict[str, dict[str, int]] = {}

    for g in genes:
        src = g.get("_source", "unknown")
        cat = g.get("category", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1
        by_source_category.setdefault(src, {})
        by_source_category[src][cat] = by_source_category[src].get(cat, 0) + 1

    signal_freq: dict[str, int] = {}
    for g in genes:
        for sig in g.get("signals_match", []):
            dim = sig.split(":")[0] if ":" in sig else sig
            signal_freq[dim] = signal_freq.get(dim, 0) + 1

    return {
        "total": len(genes),
        "by_source": by_source,
        "by_category": by_category,
        "by_source_category": by_source_category,
        "signal_dimensions": dict(sorted(signal_freq.items(), key=lambda x: -x[1])),
    }


frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True)
