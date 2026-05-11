"""
Async batch extractor — classify user prompts via Qwen on DashScope.

Pipeline
--------
1. Walk examples/{wzp,zzj}/*.txt
2. For each .txt, split on "\\n\\n---\\n\\n" → list of raw user prompts
3. For each prompt, ask qwen-plus-latest (enable_thinking=False) to return
   classification JSON (see prompts.SYSTEM_PROMPT)
4. Save the aggregated result to examples/{project}/<hash>.json
5. Snapshot: skip any session whose .json already exists and is valid

Concurrency
-----------
asyncio.Semaphore(3) — at most 3 in-flight LLM calls at any moment, across
all sessions and all prompts.

Resilience
----------
- Exponential backoff on transient errors (rate limit, timeout, 5xx)
- Per-prompt JSON repair attempt before giving up
- Session-level snapshot: writing the .json is the commit; partial sessions
  are not persisted
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

from prompts import SYSTEM_PROMPT, build_user_prompt

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_ROOT = ROOT / "examples"
PROJECTS = ("wzp", "zzj")
SPLIT_RE = re.compile(r"\n\n---\n\n")
DEFAULT_MODEL = "qwen-plus-latest"
DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MAX_CONCURRENCY = 3
PER_CALL_TIMEOUT = 60.0
MAX_RETRIES = 4


@dataclass
class PromptResult:
    index: int
    raw: str
    classification: dict[str, Any] | None
    error: str | None = None


def split_prompts(text: str) -> list[str]:
    """Split a .txt file into individual user prompts."""
    return [p.strip() for p in SPLIT_RE.split(text) if p.strip()]


def is_session_done(out_path: Path, expected_count: int) -> bool:
    """Snapshot check: session is done if output JSON exists and matches count."""
    if not out_path.exists():
        return False
    try:
        data = json.loads(out_path.read_text(encoding="utf-8"))
        return (
            isinstance(data, dict)
            and isinstance(data.get("prompts"), list)
            and len(data["prompts"]) == expected_count
            and all(p.get("classification") is not None for p in data["prompts"])
        )
    except Exception:
        return False


def coerce_json(text: str) -> dict[str, Any]:
    """Parse JSON from a model response, tolerating code fences / leading text."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # Find the outermost {...}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object found in response: {text[:200]!r}")
    return json.loads(text[start : end + 1])


async def classify_one(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    model: str,
    raw: str,
    label: str,
) -> dict[str, Any]:
    """Classify one prompt with retry. Returns the parsed JSON dict."""
    async with semaphore:
        last_err: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_user_prompt(raw)},
                    ],
                    temperature=0.1,
                    top_p=0.9,
                    timeout=PER_CALL_TIMEOUT,
                    response_format={"type": "json_object"},
                    extra_body={"enable_thinking": False},
                )
                content = resp.choices[0].message.content or ""
                return coerce_json(content)
            except (RateLimitError, APITimeoutError) as e:
                last_err = e
                wait = min(2**attempt, 30) + 0.5 * attempt
                print(
                    f"  [{label}] retryable {type(e).__name__} attempt {attempt}/{MAX_RETRIES} — sleeping {wait:.1f}s",
                    flush=True,
                )
                await asyncio.sleep(wait)
            except APIError as e:
                last_err = e
                if attempt == MAX_RETRIES:
                    raise
                wait = min(2**attempt, 30)
                print(
                    f"  [{label}] APIError attempt {attempt}/{MAX_RETRIES} — sleeping {wait:.1f}s ({e})",
                    flush=True,
                )
                await asyncio.sleep(wait)
            except (json.JSONDecodeError, ValueError) as e:
                last_err = e
                if attempt == MAX_RETRIES:
                    raise
                print(
                    f"  [{label}] parse error attempt {attempt}/{MAX_RETRIES} — retrying",
                    flush=True,
                )
                await asyncio.sleep(1.0)
        assert last_err is not None
        raise last_err


async def process_session(
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
    model: str,
    project: str,
    txt_path: Path,
) -> tuple[str, str]:
    """Process a single session .txt → session .json. Returns (status, msg)."""
    session_id = txt_path.stem
    out_path = txt_path.with_suffix(".json")
    text = txt_path.read_text(encoding="utf-8")
    prompts = split_prompts(text)

    if not prompts:
        return ("skip-empty", f"{project}/{session_id}")

    if is_session_done(out_path, len(prompts)):
        return ("skip-done", f"{project}/{session_id} ({len(prompts)} prompts)")

    print(
        f"→ start {project}/{session_id} ({len(prompts)} prompts)",
        flush=True,
    )
    t0 = time.time()

    tasks = [
        classify_one(
            client,
            semaphore,
            model,
            raw,
            label=f"{project}/{session_id}#{i}",
        )
        for i, raw in enumerate(prompts)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    rendered: list[dict[str, Any]] = []
    n_err = 0
    for i, (raw, res) in enumerate(zip(prompts, results)):
        if isinstance(res, Exception):
            n_err += 1
            rendered.append(
                {
                    "index": i,
                    "raw": raw,
                    "classification": None,
                    "error": f"{type(res).__name__}: {res}",
                }
            )
        else:
            rendered.append(
                {
                    "index": i,
                    "raw": raw,
                    "classification": res,
                    "error": None,
                }
            )

    if n_err:
        print(
            f"⚠ {project}/{session_id}: {n_err}/{len(prompts)} prompts failed — NOT writing snapshot",
            flush=True,
        )
        return ("partial-fail", f"{project}/{session_id}: {n_err} errors")

    payload = {
        "session_id": session_id,
        "project": project,
        "model": model,
        "prompt_count": len(prompts),
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompts": rendered,
    }
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out_path)
    dt = time.time() - t0
    print(
        f"✓ done {project}/{session_id} — {len(prompts)} prompts in {dt:.1f}s",
        flush=True,
    )
    return ("ok", f"{project}/{session_id}")


async def main_async(args: argparse.Namespace) -> int:
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("ERROR: DASHSCOPE_API_KEY env var is not set", file=sys.stderr)
        return 2

    client = AsyncOpenAI(api_key=api_key, base_url=DASHSCOPE_BASE)
    semaphore = asyncio.Semaphore(args.concurrency)

    targets: list[tuple[str, Path]] = []
    for project in PROJECTS:
        proj_dir = EXAMPLES_ROOT / project
        if not proj_dir.exists():
            print(f"⚠ skipping missing dir: {proj_dir}", flush=True)
            continue
        for txt in sorted(proj_dir.glob("*.txt")):
            if args.only and txt.stem not in args.only:
                continue
            targets.append((project, txt))

    print(
        f"=== extract.py — {len(targets)} session(s), model={args.model}, "
        f"max-concurrency={args.concurrency} ===",
        flush=True,
    )

    # Process sessions sequentially ("one by one" per user request).
    # Within each session, prompts are dispatched concurrently but bounded by
    # the global semaphore so total in-flight calls never exceed --concurrency.
    summary: dict[str, int] = {}
    for project, txt in targets:
        try:
            status, msg = await process_session(
                client, semaphore, args.model, project, txt
            )
        except Exception as e:
            status, msg = ("crash", f"{project}/{txt.stem}: {e}")
            print(f"✗ crash {msg}", flush=True)
        summary[status] = summary.get(status, 0) + 1

    print("\n=== summary ===", flush=True)
    for k, v in sorted(summary.items()):
        print(f"  {k}: {v}", flush=True)
    return 0 if summary.get("crash", 0) == 0 and summary.get("partial-fail", 0) == 0 else 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--concurrency", type=int, default=MAX_CONCURRENCY)
    p.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional list of session ids (file stems) to process; default = all.",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(main_async(args)))
