"""Generate index.md for each plugin subdirectory from genes.json.

Usage:
    python3 gen_index.py                          # default: ./plugins
    python3 gen_index.py --plugins-dir claude-acc/plugins
"""
import argparse
import json
from pathlib import Path


def generate_indexes(plugins_dir: Path):
    count = 0
    for d in sorted(plugins_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        genes_file = d / "genes.json"
        if not genes_file.exists():
            continue
        genes = json.loads(genes_file.read_text())

        lines = [f"# {d.name} — Gene Index", "", f"**Gene count:** {len(genes)}", ""]
        lines.append("| # | ID | Title | Category | Sessions | Signals (top 3) |")
        lines.append("|---|---|---|---|---|---|")

        for i, g in enumerate(genes, 1):
            gid = g["id"]
            title = g.get("title_en", g.get("title_zh", ""))
            cat = g.get("category", "")
            sessions = g.get("_provenance", {}).get("session_hashes", [])
            session_str = ", ".join(sessions[:3])
            if len(sessions) > 3:
                session_str += f" +{len(sessions)-3}"
            scount = g.get("_provenance", {}).get("session_count", len(sessions))
            signals = g.get("signals_match", [])[:3]
            signals_str = ", ".join(f"`{s}`" for s in signals)
            lines.append(
                f"| {i} | `{gid}` | {title} | {cat} | {scount}x: {session_str} | {signals_str} |"
            )

        lines.append("")
        lines.append("---")
        lines.append("")

        for g in genes:
            gid = g["id"]
            lines.append(f"## `{gid}`")
            lines.append("")
            lines.append(f"**{g.get('title_zh', '')}** / {g.get('title_en', '')}")
            lines.append("")
            lines.append(f"Category: `{g.get('category', '')}`")
            lines.append("")
            lines.append("**Signals:**")
            for s in g.get("signals_match", []):
                lines.append(f"- `{s}`")
            lines.append("")
            lines.append("**Preconditions:**")
            for p in g.get("preconditions", []):
                lines.append(f"- {p}")
            lines.append("")
            prov = g.get("_provenance", {})
            lines.append(f"**Evidence:** {prov.get('evidence', '')}")
            lines.append("")
            lines.append("---")
            lines.append("")

        index_path = d / "index.md"
        index_path.write_text("\n".join(lines), encoding="utf-8")
        count += 1
        print(f"  {index_path} ({len(genes)} genes)")

    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=Path(__file__).parent / "plugins",
        help="Path to the plugins directory (default: ./plugins)",
    )
    args = parser.parse_args()

    if not args.plugins_dir.exists():
        print(f"plugins dir not found: {args.plugins_dir}")
        return
    n = generate_indexes(args.plugins_dir)
    print(f"  ({n} categories indexed)")


if __name__ == "__main__":
    main()
