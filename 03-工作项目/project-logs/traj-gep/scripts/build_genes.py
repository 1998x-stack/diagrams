"""Stage 4 — translate clusters into evolver-schema Gene objects."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

CONSTRAINTS_DEFAULT = {"max_files": 10, "forbidden_paths": [".git", "node_modules"]}


@dataclass
class GeneBuilderConfig:
    max_signals_match: int = 8
    max_strategy_steps: int = 6
    include_provenance: bool = True
    provenance_session_sample: int = 5


# ----------------------------------------------------------------- helpers


def _slug(text: str, limit: int = 40) -> str:
    keep = []
    for ch in text.lower():
        if ch.isalnum():
            keep.append(ch)
        elif ch in {"_", "-"}:
            keep.append("_")
        else:
            keep.append("_")
    out = "".join(keep).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out[:limit].strip("_") or "x"


def _gene_id(project: str, cluster: dict) -> str:
    fam_token = {"F1": "f1sig", "F2": "f2flow", "F3": "f3phase"}[cluster["family"]]
    key = cluster["key"]
    if cluster["family"] == "F1":
        slug = _slug("_".join([key.get("signal", "x"), *key.get("tools", [])]))
    elif cluster["family"] == "F2":
        slug = _slug("_".join(key.get("tools", [])))
    else:
        slug = _slug("_".join([key.get("from_phase", "x"), "to",
                               key.get("to_phase", "x"), key.get("signal", "x")]))
    full = f"gene_traj_{project}_{fam_token}_{slug}"
    return full[:60]


def _signals_match(cluster: dict, cfg: GeneBuilderConfig) -> list[str]:
    fam = cluster["family"]
    key = cluster["key"]
    out: list[str] = []
    if fam == "F1":
        out.append(key["signal"])
        out.extend(cluster.get("signal_details", [])[:3])
        out.extend(t.lower() for t in key.get("tools", []))
    elif fam == "F2":
        out.extend(t.lower() for t in key.get("tools", []))
        out.append("workflow")
    elif fam == "F3":
        out.append("phase_transition")
        out.append(f"from:{key.get('from_phase')}")
        out.append(f"to:{key.get('to_phase')}")
        out.append(key.get("signal", ""))
    extras = (cluster.get("llm") or {}).get("extra_signals") or []
    out.extend(extras[:3])
    seen = set()
    deduped = []
    for s in out:
        if s and s not in seen:
            deduped.append(s)
            seen.add(s)
    return deduped[: cfg.max_signals_match]


# --------------------------------------------------------- fallback templates


def fallback_preconditions(cluster: dict) -> list[str]:
    fam = cluster["family"]
    key = cluster["key"]
    if fam == "F1":
        return [
            f"signals contains '{key.get('signal')}' indicator",
            f"task involves {key['tools'][0]} followed by {key['tools'][1]}",
            f"evidence: pattern observed in {cluster['session_count']} sessions "
            f"({cluster['frequency']} occurrences)",
        ]
    if fam == "F2":
        a, b, c = key["tools"]
        return [
            "task is in workflow phase",
            f"{a} → {b} → {c} sequence is appropriate",
            "no critical errors blocking baseline workflow",
        ]
    return [
        f"current phase is '{key.get('from_phase')}'",
        f"signals indicate transition trigger '{key.get('signal')}'",
        f"next phase '{key.get('to_phase')}' has not yet started",
    ]


def fallback_strategy(cluster: dict, cfg: GeneBuilderConfig) -> list[str]:
    fam = cluster["family"]
    key = cluster["key"]
    if fam == "F1":
        a, b = key["tools"]
        steps = [
            f"Detect '{key.get('signal')}' signal in incoming task or recent log",
            f"Apply {a} → {b} sequence as primary action path",
            f"If {a} reveals additional context, repeat before applying {b}",
            "Record outcome via EvolutionEvent for selector feedback",
        ]
    elif fam == "F2":
        a, b, c = key["tools"]
        steps = [
            f"When entering workflow phase, follow {a} → {b} → {c} as canonical flow",
            "Validate intermediate state after each tool before proceeding",
            f"Do not skip {b} even if {a} appears successful",
        ]
    else:
        steps = [
            f"Recognize transition trigger from '{key.get('from_phase')}' to "
            f"'{key.get('to_phase')}' on '{key.get('signal')}'",
            f"Complete pending {key.get('from_phase')} actions before transitioning",
            f"Initialize {key.get('to_phase')} with the file targets from "
            f"{key.get('from_phase')}",
        ]
    if cluster.get("correction_evidence"):
        top = cluster["correction_evidence"][0]
        if fam == "F1":
            tail_tool = key["tools"][1]
        elif fam == "F2":
            tail_tool = key["tools"][-1]
        else:
            tail_tool = "the transition"
        steps.append(
            f"Watch for user corrections like {top!r}; rollback {tail_tool} if triggered"
        )
    return steps[: cfg.max_strategy_steps]


# ----------------------------------------------------------------- builder


def build_gene_from_cluster(cluster: dict, *, project: str,
                            cfg: GeneBuilderConfig) -> dict:
    llm_payload = cluster.get("_gene_llm")
    if isinstance(llm_payload, dict) and not llm_payload.get("_fallback"):
        preconds = list(llm_payload.get("preconditions") or [])
        strat = list(llm_payload.get("strategy") or [])
        if not preconds:
            preconds = fallback_preconditions(cluster)
        if not strat:
            strat = fallback_strategy(cluster, cfg)
        strat = strat[: cfg.max_strategy_steps]
    else:
        preconds = fallback_preconditions(cluster)
        strat = fallback_strategy(cluster, cfg)

    gene = {
        "type": "Gene",
        "id": _gene_id(project, cluster),
        "category": cluster.get("category", "optimize"),
        "signals_match": _signals_match(cluster, cfg),
        "preconditions": preconds,
        "strategy": strat,
        "constraints": copy.deepcopy(CONSTRAINTS_DEFAULT),
        "validation": [],
    }
    llm_meta = cluster.get("llm") or {}
    if llm_meta.get("title_zh"):
        gene["title_zh"] = llm_meta["title_zh"]
    if llm_meta.get("title_en"):
        gene["title_en"] = llm_meta["title_en"]

    if cfg.include_provenance:
        gene["_provenance"] = {
            "source": "traj-gep",
            "project": project,
            "session_count": cluster["session_count"],
            "frequency": cluster["frequency"],
            "session_hashes_sample":
                list(cluster.get("sessions", []))[: cfg.provenance_session_sample],
        }
    return gene


# ----------------------------------------------------------------- CLI


def _build_user_payload_for_llm(cluster: dict) -> str:
    return json.dumps({
        "family": cluster["family"],
        "category": cluster["category"],
        "key": cluster["key"],
        "session_count": cluster["session_count"],
        "frequency": cluster["frequency"],
        "signal_details": cluster.get("signal_details", []),
        "representative_files": cluster.get("representative_files", []),
        "correction_evidence": cluster.get("correction_evidence", []),
        "llm_meta": cluster.get("llm") or {},
    }, ensure_ascii=False)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--clusters", required=True, type=Path)
    p.add_argument("--project", required=True,
                   help="Project label (used in output paths and LLM cache scoping).")
    p.add_argument("--config", default=Path("config.yaml"), type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--prompt-file",
                   default=Path("prompts/gene_strategy.txt"), type=Path)
    p.add_argument("--model", default=None,
                   help="Override llm.model from config.yaml (e.g., claude-sonnet-4-6).")
    args = p.parse_args(argv)

    cfg_full = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    g_cfg = cfg_full.get("gene_builder", {})
    cfg = GeneBuilderConfig(
        max_signals_match=int(g_cfg.get("max_signals_match", 8)),
        max_strategy_steps=int(g_cfg.get("max_strategy_steps", 6)),
        include_provenance=bool(g_cfg.get("include_provenance", True)),
        provenance_session_sample=int(g_cfg.get("provenance_session_sample", 5)),
    )

    clusters = json.loads(args.clusters.read_text(encoding="utf-8"))
    if not isinstance(clusters, list):
        print("clusters file is not a JSON array", file=sys.stderr)
        return 2

    # LLM gene-field generation
    from scripts.llm_client import LLMClient, load_llm_config
    llm_cfg = load_llm_config(cfg_full, model_override=args.model)
    cache_path = Path(cfg_full.get("paths", {}).get("output_dir", "./output")) \
        / args.project / "llm_cache.jsonl"
    llm = LLMClient(llm_cfg, cache_path=cache_path)
    system_prompt = args.prompt_file.read_text(encoding="utf-8")

    for c in clusters:
        user_payload = _build_user_payload_for_llm(c)
        c["_gene_llm"] = llm.call(system=system_prompt, user=user_payload)

    genes = [build_gene_from_cluster(c, project=args.project, cfg=cfg) for c in clusters]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(genes, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"wrote {len(genes)} genes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
