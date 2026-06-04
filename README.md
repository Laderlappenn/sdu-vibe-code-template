# Standardize Vibe Dashboard Skill

This repository contains one installable agent skill:

```text
standardize-vibe-dashboard/
```

The skill helps agents turn CSV-first dashboard requests into lightweight React + FastAPI + ClickHouse services with explicit `schema.table` query contracts, dashboard SQL files, Docker Compose runtime, and SDU Data Portal UI rules.

## Install

From a local clone of this repository:

```bash
python3 standardize-vibe-dashboard/scripts/install_skill.py
```

By default this installs the skill into both:

- `~/.codex/skills/standardize-vibe-dashboard`
- `~/.claude/skills/standardize-vibe-dashboard`

Install for one agent only:

```bash
python3 standardize-vibe-dashboard/scripts/install_skill.py --target codex
python3 standardize-vibe-dashboard/scripts/install_skill.py --target claude
```

Restart the agent after installation.

## Ask An Agent To Install

Give this repository to a teammate and tell their coding agent:

```text
Install the skill from this repository. The skill folder is standardize-vibe-dashboard.
```

For Codex with GitHub install support, use the repo path directly:

```text
Install the skill from https://github.com/<owner>/<repo>/tree/main/standardize-vibe-dashboard
```

## Use

After installation:

```text
Use $standardize-vibe-dashboard. I am attaching CSV files and want to vibe-code a dashboard from them.
```

For the analyst starter prompt:

```bash
cat standardize-vibe-dashboard/assets/analyst-start-prompt.md
```
