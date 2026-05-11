"""Stage 3 — cluster signals into recurring patterns and augment with LLM summaries."""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable

import yaml


# ----------------------------------------------------------------- data types


@dataclass
class ClusterConfig:
    min_sessions: int = 3
    min_frequency: int = 5  # retained in config schema; not applied by _meets() — min_distinctness already filters spammy single-session repetition
    min_distinctness: float = 0.4
    top_k_per_family: int = 30
    dedupe_jaccard: float = 0.8


@dataclass
class Cluster:
    cluster_id: str
    family: str                # "F1" / "F2" / "F3"
    category: str              # repair / optimize / innovate / workflow
    key: dict                  # family-specific
    session_count: int
    frequency: int
    sessions: list[str]
    signal_details: list[str] = field(default_factory=list)
    representative_files: list[str] = field(default_factory=list)
    correction_evidence: list[str] = field(default_factory=list)
    user_corpus_pool: list[str] = field(default_factory=list)
    llm: dict = field(default_factory=dict)


# ----------------------------------------------------------------- normalize


def normalize_signal(sig: str) -> str:
    return sig.split(":", 1)[0]


_REPAIR_SIGNALS = {"log_error", "recurring_errsig", "errsig"}
_OPTIMIZE_SIGNALS = {"perf_bottleneck", "capability_gap", "unsupported_input_type"}
_INNOVATE_SIGNALS = {"user_feature_request", "user_improvement_suggestion", "external_opportunity"}


def _category_for_signal(sig: str) -> str:
    n = normalize_signal(sig)
    if n in _REPAIR_SIGNALS:
        return "repair"
    if n in _INNOVATE_SIGNALS:
        return "innovate"
    if n in _OPTIMIZE_SIGNALS:
        return "optimize"
    return "optimize"


# ----------------------------------------------------------------- helpers


def _bigrams(seq):
    return list(zip(seq, seq[1:])) if len(seq) >= 2 else []


def _trigrams(seq):
    return list(zip(seq, seq[1:], seq[2:])) if len(seq) >= 3 else []


def _phase_transitions(phases):
    seen = set()
    out = []
    for a, b in zip(phases, phases[1:]):
        if a == b or not a or not b:
            continue
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _slug(parts: Iterable[str]) -> str:
    raw = "_".join(str(p) for p in parts)
    keep = []
    for ch in raw.lower():
        if ch.isalnum():
            keep.append(ch)
        elif ch in {"_", "-"}:
            keep.append("_")
    return "".join(keep)[:40].strip("_") or "x"


def _jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


# ----------------------------------------------------------------- clustering


def cluster_signals(sessions: list[dict], cfg: ClusterConfig) -> list[Cluster]:
    f1, f2, f3 = {}, {}, {}
    f1_details = {}
    pool_by_session = {s["session_hash"]: (s.get("user_corpus") or "") for s in sessions}
    files_by_session = {s["session_hash"]: list(s.get("file_targets") or []) for s in sessions}
    correction_by_session = {s["session_hash"]: list(s.get("correction_signals") or [])
                             for s in sessions}

    for s in sessions:
        h = s["session_hash"]
        sigs = s.get("signals") or []
        norm = sorted({normalize_signal(x) for x in sigs})
        for sig in norm:
            for a, b in _bigrams(s.get("tool_sequence") or []):
                key = (sig, a, b)
                f1.setdefault(key, []).append(h)
                f1_details.setdefault(key, set()).update(sigs)
        for a, b, c in _trigrams(s.get("tool_sequence") or []):
            f2.setdefault((a, b, c), []).append(h)
        for (p1, p2) in _phase_transitions(s.get("phase_sequence") or []):
            for sig in norm:
                f3.setdefault((p1, p2, sig), []).append(h)

    def _meets(hashes):
        return (len(set(hashes)) >= cfg.min_sessions
                and (len(set(hashes)) / len(hashes)) >= cfg.min_distinctness)

    candidates: list[Cluster] = []

    for (sig, a, b), hashes in f1.items():
        if not _meets(hashes):
            continue
        sset = sorted(set(hashes))
        candidates.append(Cluster(
            cluster_id=f"f1_{_slug([sig, a, b])}",
            family="F1", category=_category_for_signal(sig),
            key={"signal": sig, "tools": [a, b]},
            session_count=len(sset), frequency=len(hashes),
            sessions=sset,
            signal_details=sorted(f1_details.get((sig, a, b), set())),
        ))

    for (a, b, c), hashes in f2.items():
        if not _meets(hashes):
            continue
        sset = sorted(set(hashes))
        candidates.append(Cluster(
            cluster_id=f"f2_{_slug([a, b, c])}",
            family="F2", category="workflow",
            key={"tools": [a, b, c]},
            session_count=len(sset), frequency=len(hashes),
            sessions=sset,
        ))

    for (p1, p2, sig), hashes in f3.items():
        if not _meets(hashes):
            continue
        sset = sorted(set(hashes))
        candidates.append(Cluster(
            cluster_id=f"f3_{_slug([p1, p2, sig])}",
            family="F3", category="workflow",
            key={"from_phase": p1, "to_phase": p2, "signal": sig},
            session_count=len(sset), frequency=len(hashes),
            sessions=sset,
        ))

    # populate evidence
    for c in candidates:
        files: list[str] = []
        for h in c.sessions:
            for fp in files_by_session.get(h, []):
                if fp not in files:
                    files.append(fp)
        c.representative_files = files[:10]
        evid: list[str] = []
        for h in c.sessions:
            for cs in correction_by_session.get(h, []):
                if cs not in evid:
                    evid.append(cs)
        c.correction_evidence = evid[:5]
        c.user_corpus_pool = [pool_by_session.get(h, "") for h in c.sessions
                              if pool_by_session.get(h)]

    # top-k per family
    by_fam: dict[str, list[Cluster]] = {}
    for c in candidates:
        by_fam.setdefault(c.family, []).append(c)
    capped: list[Cluster] = []
    for fam, items in by_fam.items():
        items.sort(key=lambda x: -x.session_count)
        capped.extend(items[: cfg.top_k_per_family])

    # dedupe overlapping (same signal-share + jaccard above threshold)
    capped.sort(key=lambda x: -x.session_count)
    kept: list[Cluster] = []
    for c in capped:
        keep = True
        for k in kept:
            if k.family != c.family:
                continue
            shares_signal = (
                c.key.get("signal") and k.key.get("signal") == c.key.get("signal")
            ) or (c.family == "F2" and k.key.get("tools") == c.key.get("tools"))
            if shares_signal and _jaccard(c.sessions, k.sessions) > cfg.dedupe_jaccard:
                keep = False
                break
        if keep:
            kept.append(c)
    return kept


# ----------------------------------------------------------------- LLM augment


def sample_excerpts(seed: str, pool: list[str], *, count: int, max_chars: int) -> list[str]:
    rnd = random.Random(seed)
    pool = [p for p in pool if p]
    if not pool:
        return []
    chosen = rnd.sample(pool, min(count, len(pool)))
    return [p[:max_chars] for p in chosen]


def augment_with_llm(clusters: list[Cluster], sessions: list[dict], llm,
                     *, system_prompt: str, excerpt_count: int, excerpt_max_chars: int
                     ) -> list[Cluster]:
    for c in clusters:
        excerpts = sample_excerpts(
            c.cluster_id, c.user_corpus_pool,
            count=excerpt_count, max_chars=excerpt_max_chars,
        )
        user_payload = json.dumps({
            "family": c.family,
            "key": c.key,
            "session_count": c.session_count,
            "frequency": c.frequency,
            "signal_details": c.signal_details,
            "user_corpus_excerpts": excerpts,
            "representative_files": c.representative_files,
            "correction_evidence": c.correction_evidence,
        }, ensure_ascii=False)
        payload = llm.call(system=system_prompt, user=user_payload)
        if isinstance(payload, dict) and not payload.get("_fallback"):
            c.llm = {
                "title_zh": payload.get("title_zh", "")[:60],
                "title_en": payload.get("title_en", "")[:120],
                "summary_zh": payload.get("summary_zh", "")[:240],
                "extra_signals": [s for s in (payload.get("extra_signals") or [])
                                  if isinstance(s, str)][:3],
            }
        else:
            c.llm = {"title_zh": "", "title_en": "", "summary_zh": "",
                     "extra_signals": [], "_fallback": True}
    return clusters


# ----------------------------------------------------------------- CLI


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--signals-file", required=True, type=Path)
    p.add_argument("--config", default=Path("config.yaml"), type=Path)
    p.add_argument("--project", required=True,
                   help="Project label (used in output paths and LLM cache scoping).")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--prompt-file",
                   default=Path("prompts/cluster_summary.txt"), type=Path)
    p.add_argument("--model", default=None,
                   help="Override llm.model from config.yaml (e.g., claude-sonnet-4-6).")
    args = p.parse_args(argv)

    cfg_full = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    cl = cfg_full.get("clustering", {})
    cfg = ClusterConfig(
        min_sessions=int(cl.get("min_sessions", 3)),
        min_frequency=int(cl.get("min_frequency", 5)),
        min_distinctness=float(cl.get("min_distinctness", 0.4)),
        top_k_per_family=int(cl.get("top_k_per_family", 30)),
        dedupe_jaccard=float(cl.get("dedupe_jaccard", 0.8)),
    )

    sessions = []
    with args.signals_file.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                sessions.append(json.loads(line))

    clusters = cluster_signals(sessions, cfg)
    print(f"rule-based clusters: {len(clusters)}", file=sys.stderr)

    # LLM augmentation
    from scripts.llm_client import LLMClient, load_llm_config
    llm_cfg = load_llm_config(cfg_full, model_override=args.model)
    cache_path = Path(cfg_full.get("paths", {}).get("output_dir", "./output")) \
        / args.project / "llm_cache.jsonl"
    llm = LLMClient(llm_cfg, cache_path=cache_path)
    system_prompt = args.prompt_file.read_text(encoding="utf-8")

    excerpt_count = int(cfg_full.get("llm", {}).get("cluster_excerpt_count", 5))
    excerpt_max = int(cfg_full.get("llm", {}).get("cluster_excerpt_max_chars", 400))

    augment_with_llm(clusters, sessions, llm,
                     system_prompt=system_prompt,
                     excerpt_count=excerpt_count,
                     excerpt_max_chars=excerpt_max)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps([asdict(c) for c in clusters], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {len(clusters)} clusters to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
