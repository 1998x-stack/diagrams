import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TRAJ_GEP = REPO / "traj-gep"
TRAJ_DATA = REPO / "traj-data-new" / "wzp"


def _node_available() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


@pytest.mark.skipif(not _node_available(), reason="node not installed")
@pytest.mark.skipif(not TRAJ_DATA.exists(), reason="real wzp traj data not present")
def test_full_pipeline_on_3_real_traj_files(tmp_path, monkeypatch):
    """End-to-end smoke test:
    - copies 3 real .traj files into a tmp project tree
    - pre-seeds the LLM cache so no live Dashscope call is made
    - runs all four stages via subprocess
    - asserts final genes.json is a valid JSON array
    """
    sample = sorted(TRAJ_DATA.glob("*.traj"))[:3]
    if len(sample) < 3:
        pytest.skip("need 3 real wzp .traj files for smoke test")

    # ------------------------------------------------------------------ tree
    work = tmp_path / "work"
    (work / "traj-data-new" / "wzp").mkdir(parents=True)
    for f in sample:
        shutil.copy(f, work / "traj-data-new" / "wzp" / f.name)
    # symlink evolver and traj-gep instead of copying (saves time)
    (work / "evolver").symlink_to(REPO / "evolver", target_is_directory=True)
    shutil.copytree(TRAJ_GEP, work / "traj-gep")
    out_dir = work / "traj-gep" / "output" / "wzp"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ cache
    # Use a sitecustomize shim to replace LLMClient._create_chat_completion
    # with a deterministic stub. This avoids any live API call from the
    # subprocess-launched stages.
    sitecustom = work / "sitecustomize.py"
    sitecustom.write_text(
        "import scripts.llm_client as _l\n"
        "_orig = _l.LLMClient\n"
        "class _Fake(_orig):\n"
        "    def _create_chat_completion(self, system, user):\n"
        "        if 'preconditions' in system:\n"
        "            return {'preconditions':['脑力大冒险测试条件'],"
        "'strategy':['步骤一: Read','步骤二: Edit']}\n"
        "        return {'title_zh':'测试','title_en':'test',"
        "'summary_zh':'测试摘要','extra_signals':['cn_smoke']}\n"
        "_l.LLMClient = _Fake\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{work}:{work / 'traj-gep'}"
    env["DASHSCOPE_API_KEY"] = "sk-smoke-fake"

    # ---------------------------------------------------------------- run all
    def _run(cmd):
        subprocess.run(cmd, cwd=work / "traj-gep", env=env,
                       capture_output=True, text=True, check=True, timeout=120)

    _run([sys.executable, "-m", "scripts.load_trajectories",
          "--traj-dir", str(work / "traj-data-new" / "wzp"),
          "--project", "wzp",
          "--output", str(out_dir / "sessions.jsonl")])
    _run([sys.executable, "-m", "scripts.extract_signals",
          "--sessions-file", str(out_dir / "sessions.jsonl"),
          "--wrapper", str(work / "traj-gep" / "scripts" / "extract_signals.js"),
          "--output", str(out_dir / "signals.jsonl"),
          "--config", str(work / "traj-gep" / "config.yaml")])
    _run([sys.executable, "-m", "scripts.cluster_patterns",
          "--signals-file", str(out_dir / "signals.jsonl"),
          "--project", "wzp",
          "--config", str(work / "traj-gep" / "config.yaml"),
          "--output", str(out_dir / "clusters.json")])
    _run([sys.executable, "-m", "scripts.build_genes",
          "--clusters", str(out_dir / "clusters.json"),
          "--project", "wzp",
          "--config", str(work / "traj-gep" / "config.yaml"),
          "--output", str(out_dir / "genes.json")])

    # ---------------------------------------------------------------- assert
    text = (out_dir / "genes.json").read_text(encoding="utf-8")
    parsed = json.loads(text)
    assert isinstance(parsed, list)   # 3 sessions may not yield clusters; empty list OK
