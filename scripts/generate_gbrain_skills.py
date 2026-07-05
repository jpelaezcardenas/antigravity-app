"""Generate GBrain skill files from AGENTES.md (Contexia's canonical agent catalog).

Part of OpenSpec change `adopt-gbrain-second-brain` (capability `gbrain-adoption`, task 6.2).

AGENTES.md remains canonical (CLAUDE.md §6, symlink-integrity rule). These generated files
are a PROJECTION for GBrain's resolver, additional to GBrain's native skill modules — never
a replacement. They do not invoke anything themselves; the actual agent calls go through the
separate `contexia-agents` MCP server (see design.md Decision 5: actions vs. knowledge, two
MCP servers). A generated skill's job is purely to let GBrain's resolver answer "where does
Centinela live?" with the right endpoint/HITL/purpose reference.

Regenerate any time AGENTES.md changes (task 6.4 requires this, not manual patching):
    python scripts/generate_gbrain_skills.py --out /path/to/gbrain/skills/contexia-agents

Parses each "#### N. NAME (subtitle)" section in AGENTES.md followed by a
"| **Field** | Value |" table, extracting Endpoint / Tipo / Función canónica / HITL.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

SECTION_RE = re.compile(r"^#### (\d+[a-z]?)\.\s+(.+?)\s*(?:\((.+)\))?\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Agent:
    number: str
    name: str
    subtitle: str
    endpoint: str
    tipo: str
    funcion: str
    hitl: str

    @property
    def slug(self) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return base

    @property
    def hitl_bool(self) -> bool:
        return "sí" in self.hitl.lower() or "si" in self.hitl.lower() or "✅" in self.hitl


def parse_agents(agentes_md: str) -> list[Agent]:
    """Parse AGENTES.md sections into structured Agent records.

    Only sections followed by a field table containing "Endpoint" are treated as real
    agents — this naturally excludes the later "#### N. Tenant Membership Verification"
    style security-concerns sections, which don't have that field.
    """
    agents: list[Agent] = []
    matches = list(SECTION_RE.finditer(agentes_md))
    for i, m in enumerate(matches):
        number, name, subtitle = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(agentes_md)
        section_text = agentes_md[m.end():section_end]

        fields = {k.strip(): v.strip() for k, v in FIELD_RE.findall(section_text)}
        endpoint = fields.get("Endpoint")
        if not endpoint:
            continue  # not a real agent section (e.g., security-concerns subsection)

        agents.append(
            Agent(
                number=number,
                name=name,
                subtitle=subtitle,
                endpoint=endpoint.strip("`"),
                tipo=fields.get("Tipo", ""),
                funcion=fields.get("Función canónica", ""),
                hitl=fields.get("HITL", "unknown"),
            )
        )
    return agents


def render_skill(agent: Agent) -> str:
    triggers = [
        f'"{agent.name.lower()}"',
        f'"dónde está {agent.name.lower()}"',
        f'"where is {agent.name.lower()}"',
    ]
    triggers_yaml = "\n".join(f"  - {t}" for t in triggers)
    description = agent.funcion or agent.tipo or agent.subtitle or agent.name

    return f"""---
name: contexia-agent-{agent.slug}
version: 1.0.0
description: |
  Reference/routing skill for Contexia's {agent.name} agent — {description}.
  This does NOT invoke the agent directly (that goes through the separate
  contexia-agents MCP server). It exists so GBrain's resolver can answer
  "where does {agent.name} live?" with an accurate, canonical reference.
triggers:
{triggers_yaml}
tools: []
mutating: false
generated_from: AGENTES.md
canonical_source: antigravity-app/AGENTES.md (agent {agent.number})
---

# {agent.name}

{f"**{agent.subtitle}**" if agent.subtitle else ""}

## Reference

- **Endpoint**: `{agent.endpoint}`
- **Tipo**: {agent.tipo or "N/A"}
- **Función canónica**: {agent.funcion or "N/A"}
- **HITL required**: {"Yes" if agent.hitl_bool else "No"} ({agent.hitl})
- **Invocation**: via the `contexia-agents` MCP server (separate from GBrain's own MCP server —
  actions vs. knowledge, per design decision 5 of `adopt-gbrain-second-brain`)

## Contract

This is a **reference-only** skill. It does not call `{agent.endpoint}` itself. It supplements
GBrain's resolver so a query like "where does {agent.name} live?" or "does {agent.name} need
human approval?" resolves correctly, without duplicating or overriding `AGENTES.md`, which
remains the canonical source (regenerate this file if `AGENTES.md` changes — see
`scripts/generate_gbrain_skills.py` in `antigravity-app`).
"""


RESOLVER_MARKER_START = "<!-- BEGIN generated: contexia-agents (scripts/generate_gbrain_skills.py) -->"
RESOLVER_MARKER_END = "<!-- END generated: contexia-agents -->"


def render_resolver_section(agents: list[Agent]) -> str:
    rows = "\n".join(
        f'| "{a.name.lower()}", "dónde está {a.name.lower()}" | `skills/contexia-agent-{a.slug}/SKILL.md` |'
        for a in agents
    )
    return (
        f"{RESOLVER_MARKER_START}\n"
        "## Contexia agents (reference/routing only — regenerated, do not hand-edit)\n\n"
        "These point at Contexia's own agents (AGENTES.md is canonical; see design.md Decision 4).\n"
        "None of these invoke anything — actual calls go through the separate `contexia-agents`\n"
        "MCP server. Regenerate via `python scripts/generate_gbrain_skills.py` in `antigravity-app`\n"
        "whenever `AGENTES.md` changes.\n\n"
        "| Trigger | Skill |\n"
        "|---------|-------|\n"
        f"{rows}\n\n"
        f"{RESOLVER_MARKER_END}"
    )


def update_resolver(resolver_path: Path, agents: list[Agent], dry_run: bool) -> None:
    if not resolver_path.is_file():
        print(f"[skip] RESOLVER.md not found at {resolver_path}, not updating")
        return
    content = resolver_path.read_text(encoding="utf-8")
    new_section = render_resolver_section(agents)

    if RESOLVER_MARKER_START in content:
        pattern = re.compile(
            re.escape(RESOLVER_MARKER_START) + r".*?" + re.escape(RESOLVER_MARKER_END),
            re.DOTALL,
        )
        content = pattern.sub(new_section, content)
    else:
        # Insert before the "## Conventions" section (a stable anchor in GBrain's RESOLVER.md)
        anchor = "## Conventions (cross-cutting)"
        if anchor in content:
            content = content.replace(anchor, f"{new_section}\n\n{anchor}")
        else:
            content = content.rstrip() + f"\n\n{new_section}\n"

    if dry_run:
        print(f"[dry-run] would update {resolver_path} with {len(agents)} routing entries")
    else:
        resolver_path.write_text(content, encoding="utf-8", newline="\n")
        print(f"updated {resolver_path}")


def update_manifest(manifest_path: Path, agents: list[Agent], dry_run: bool) -> None:
    """Register generated skills in manifest.json — GBrain's `checkResolvable()` reads
    total_skills/reachability from this manifest, NOT from a filesystem scan or RESOLVER.md
    text (verified against src/core/check-resolvable.ts's loadManifest()). Without this,
    generated skills exist on disk but are invisible to `gbrain check-resolvable`/`doctor`.

    NOTE: manifest.json is a file tracked by upstream GBrain. Extending it means a future
    `git pull` on this clone will hit a merge conflict here (not silent data loss, but real
    manual-reconciliation work) — a small, deliberate exception to the "don't fork GBrain"
    decision, necessary because GBrain has no external-skill-registration mechanism for
    markdown skills (only for MCP tool plugins, via GBRAIN_PLUGIN_PATH).
    """
    if not manifest_path.is_file():
        print(f"[skip] manifest.json not found at {manifest_path}, not updating")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing_names = {s["name"] for s in manifest["skills"]}

    added = 0
    for agent in agents:
        name = f"contexia-agent-{agent.slug}"
        if name in existing_names:
            continue  # already registered from a prior run
        manifest["skills"].append(
            {
                "name": name,
                "path": f"contexia-agent-{agent.slug}/SKILL.md",
                "description": f"Reference/routing skill for Contexia's {agent.name} agent (generated from AGENTES.md, not hand-edited)",
            }
        )
        added += 1

    if dry_run:
        print(f"[dry-run] would add {added} new entries to {manifest_path}")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"updated {manifest_path} (+{added} entries)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentes-md", default="AGENTES.md", help="Path to AGENTES.md")
    parser.add_argument("--out", required=True, help="Output directory for generated skill files")
    parser.add_argument("--resolver", default=None, help="Path to GBrain's RESOLVER.md to update (optional)")
    parser.add_argument("--manifest", default=None, help="Path to GBrain's skills/manifest.json to update (optional)")
    parser.add_argument("--dry-run", action="store_true", help="List what would be generated, without writing")
    args = parser.parse_args()

    agentes_md = Path(args.agentes_md).read_text(encoding="utf-8")
    agents = parse_agents(agentes_md)

    out_dir = Path(args.out)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    for agent in agents:
        # GBrain's real convention: one directory per skill, containing SKILL.md
        # (verified against skills/query/SKILL.md in the installed tool — NOT flat files).
        skill_dir = out_dir / f"contexia-agent-{agent.slug}"
        target = skill_dir / "SKILL.md"
        if args.dry_run:
            print(f"[dry-run] would write {target} (endpoint={agent.endpoint}, hitl={agent.hitl_bool})")
        else:
            skill_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(render_skill(agent), encoding="utf-8", newline="\n")
            print(f"wrote {target}")

    if args.resolver:
        update_resolver(Path(args.resolver), agents, args.dry_run)
    if args.manifest:
        update_manifest(Path(args.manifest), agents, args.dry_run)

    print(f"\n{len(agents)} agent skill(s) {'would be ' if args.dry_run else ''}generated from {args.agentes_md}")


if __name__ == "__main__":
    main()
