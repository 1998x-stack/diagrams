"""Stage 5 — cluster duplicate Genes via LLM, write cleaned_genes.json."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import yaml


# --------------------------------------------------------------- prompt build


def build_user_payload(category: str, genes: list[dict]) -> str:
    """Compact per-category summary sent to the LLM."""
    summary = [{
        "id": g["id"],
        "title_zh": g.get("title_zh", ""),
        "title_en": g.get("title_en", ""),
        "frequency": int((g.get("_provenance") or {}).get("frequency", 0)),
        "preconditions": list(g.get("preconditions", []))[:5],
    } for g in genes]
    # First line is parseable by tests: `category=<name>`
    return f"category={category}\n" + json.dumps(
        {"genes": summary}, ensure_ascii=False, indent=2,
    )


# --------------------------------------------------------------- merging


def _merge_strings(lists: Iterable[list[str]], cap: int | None = None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for lst in lists:
        for item in lst or []:
            if item and item not in seen:
                out.append(item)
                seen.add(item)
                if cap is not None and len(out) >= cap:
                    return out
    return out


def merge_cluster(members: list[dict], *, new_title_zh: str, new_title_en: str,
                  max_signals: int, max_strategy: int,
                  provenance_sample: int) -> dict:
    """Build a merged Gene from cluster members.

    Singleton clusters keep their original id and (if LLM titles are empty) original titles.
    """
    assert members, "merge_cluster called with no members"
    members_sorted = sorted(members,
                            key=lambda g: int((g.get("_provenance") or {}).get("frequency", 0)),
                            reverse=True)
    rep = members_sorted[0]

    is_singleton = len(members) == 1
    title_zh = new_title_zh or rep.get("title_zh", "")
    title_en = new_title_en or rep.get("title_en", "")

    if is_singleton:
        merged_id = rep["id"]
    else:
        merged_id = f"{rep['id']}_merged_{len(members)}"
        merged_id = merged_id[:80]

    max_files = max((m.get("constraints", {}).get("max_files", 0) or 0) for m in members)
    forbidden = sorted({p for m in members
                        for p in (m.get("constraints", {}).get("forbidden_paths") or [])})

    freq_sum = sum(int((m.get("_provenance") or {}).get("frequency", 0)) for m in members)
    sc_sum = sum(int((m.get("_provenance") or {}).get("session_count", 0)) for m in members)
    sessions = _merge_strings(
        ((m.get("_provenance") or {}).get("session_hashes_sample") or [] for m in members),
        cap=provenance_sample,
    )
    sessions.sort()

    prov = {
        "source": "traj-gep",
        "project": (rep.get("_provenance") or {}).get("project", ""),
        "session_count": sc_sum,
        "frequency": freq_sum,
        "session_hashes_sample": sessions,
    }
    if not is_singleton:
        prov["_merged_from"] = sorted(m["id"] for m in members)

    return {
        "type": "Gene",
        "id": merged_id,
        "category": rep["category"],
        "signals_match": _merge_strings((m.get("signals_match", []) for m in members),
                                        cap=max_signals),
        "preconditions": _merge_strings(m.get("preconditions", []) for m in members),
        "strategy": _merge_strings((m.get("strategy", []) for m in members),
                                   cap=max_strategy),
        "constraints": {"max_files": int(max_files) if max_files else 10,
                        "forbidden_paths": forbidden or [".git", "node_modules"]},
        "validation": _merge_strings(m.get("validation", []) for m in members),
        "title_zh": title_zh,
        "title_en": title_en,
        "_provenance": prov,
    }


# --------------------------------------------------------------- clustering


def _validate_and_recover(payload: dict, input_ids: list[str]) -> list[dict]:
    """Return list of clusters with `ids`, `new_title_zh`, `new_title_en`. Recover from drift."""
    clusters = (payload or {}).get("clusters") or []
    seen: set[str] = set()
    out: list[dict] = []
    valid_ids = set(input_ids)
    for c in clusters:
        ids = [i for i in (c.get("ids") or []) if i in valid_ids and i not in seen]
        if not ids:
            continue
        seen.update(ids)
        out.append({
            "ids": ids,
            "new_title_zh": (c.get("new_title_zh") or "").strip(),
            "new_title_en": (c.get("new_title_en") or "").strip(),
        })

    missing = [i for i in input_ids if i not in seen]
    if missing:
        print(f"clean_genes: WARN {len(missing)} missing ids from LLM; emitting as singletons: "
              f"{missing[:5]}{'...' if len(missing) > 5 else ''}", file=sys.stderr)
        for mid in missing:
            out.append({"ids": [mid], "new_title_zh": "", "new_title_en": ""})
    return out


def cluster_genes(genes: list[dict], *, llm, system_prompt: str,
                  min_titles_for_llm: int, prompt_max_genes_per_call: int,
                  max_signals: int = 8, max_strategy: int = 6,
                  provenance_sample: int = 5) -> list[dict]:
    """Group genes by category, ask LLM to cluster each group, merge and return cleaned genes."""
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for g in genes:
        by_cat[g.get("category", "unknown")].append(g)

    by_id = {g["id"]: g for g in genes}
    cleaned: list[dict] = []

    for category, group in by_cat.items():
        if len(group) < min_titles_for_llm:
            for g in group:
                cleaned.append(merge_cluster([g],
                                             new_title_zh="", new_title_en="",
                                             max_signals=max_signals,
                                             max_strategy=max_strategy,
                                             provenance_sample=provenance_sample))
            continue

        chunk_size = max(1, prompt_max_genes_per_call)
        for i in range(0, len(group), chunk_size):
            chunk = group[i:i + chunk_size]
            user_payload = build_user_payload(category, chunk)
            payload = llm.call(system=system_prompt, user=user_payload)
            if payload.get("_fallback"):
                print(f"clean_genes: WARN LLM fallback for category={category}; "
                      "keeping all members as singletons", file=sys.stderr)
                clusters = [{"ids": [g["id"]], "new_title_zh": "", "new_title_en": ""}
                            for g in chunk]
            else:
                clusters = _validate_and_recover(payload, [g["id"] for g in chunk])

            for c in clusters:
                members = [by_id[i] for i in c["ids"]]
                cleaned.append(merge_cluster(
                    members,
                    new_title_zh=c["new_title_zh"], new_title_en=c["new_title_en"],
                    max_signals=max_signals, max_strategy=max_strategy,
                    provenance_sample=provenance_sample,
                ))

    cleaned.sort(key=lambda g: (-int(g["_provenance"]["frequency"]), g["id"]))
    return cleaned


# --------------------------------------------------------------- CLI


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--genes", required=True, type=Path)
    p.add_argument("--project", required=True,
                   help="Project label (used in LLM cache scoping).")
    p.add_argument("--config", default=Path("config.yaml"), type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--prompt-file", default=Path("prompts/clean_genes.txt"), type=Path)
    p.add_argument("--model", default=None,
                   help="Override llm.model from config.yaml.")
    args = p.parse_args(argv)

    cfg_full = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    cleaning = cfg_full.get("cleaning", {})
    g_cfg = cfg_full.get("gene_builder", {})

    genes = json.loads(args.genes.read_text(encoding="utf-8"))
    if not isinstance(genes, list):
        print("genes file is not a JSON array", file=sys.stderr)
        return 2

    from scripts.llm_client import LLMClient, load_llm_config
    llm_cfg = load_llm_config(cfg_full, model_override=args.model)
    cache_path = Path(cfg_full.get("paths", {}).get("output_dir", "./output")) \
        / args.project / "llm_cache.jsonl"
    llm = LLMClient(llm_cfg, cache_path=cache_path)
    system_prompt = args.prompt_file.read_text(encoding="utf-8")

    cleaned = cluster_genes(
        genes, llm=llm, system_prompt=system_prompt,
        min_titles_for_llm=int(cleaning.get("min_titles_for_llm", 2)),
        prompt_max_genes_per_call=int(cleaning.get("prompt_max_genes_per_call", 80)),
        max_signals=int(g_cfg.get("max_signals_match", 8)),
        max_strategy=int(g_cfg.get("max_strategy_steps", 6)),
        provenance_sample=int(g_cfg.get("provenance_session_sample", 5)),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"wrote {len(cleaned)} cleaned genes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
