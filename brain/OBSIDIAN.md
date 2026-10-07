# Obsidian as a second brain: worth it?

## Short answer
**Yes, but as a window onto this repo, not as a second, separate system.**
Obsidian is a free app that shows a folder of Markdown (.md) files as linked notes, tables and boards. This repo
already IS a folder of Markdown files (PROJECT-MEMORY.md, campaigns, research, scripts). So:

- Open the `kids-coloring-books` folder as an Obsidian **vault**. No copying, no migration.
- Claude keeps writing the same .md files; the owner reads and edits them in Obsidian. GitHub stays the backup/sync.
- Don't keep a separate Obsidian vault with different notes: two "brains" drift apart and Claude only reads one.

## What it adds for us
- A nice place to **read** everything (instead of GitHub on a phone): research, plans, captions, the week.
- **Graph / links:** book ↔ campaign ↔ ad ↔ result.
- **Dataview tables:** if every ad note has properties (book, format, hook, platform, views, clicks), Obsidian can
  show live tables like "all guess-the-colors videos sorted by link clicks". That's a mini dashboard.
- **Kanban board:** ideas → script → rendered → scheduled → posted → measured.
- **Daily note:** what was posted today + numbers, which Claude can read next session.

## What it does NOT do
- It doesn't make Claude smarter by itself; Claude already reads the repo. The gain is for the owner (overview, speed).
- It doesn't collect platform stats; the numbers still come from exports (see DASHBOARD-PLAN.md).

## Suggested setup at home (ask before installing)
1. Install Obsidian (obsidian.md, free), "Open folder as vault" → the repo folder.
2. Community plugins: **Obsidian Git** (auto pull/commit/push), **Dataview** (tables from note properties),
   **Templater** (templates for new ad notes / books), **Kanban** (production board).
3. Folder conventions: `ads/` one note per ad (properties: date, platform, book, format, hook, file, views_3d,
   watch_pct, clicks, verdict) · `books/` · `campaigns/` · `daily/YYYY-MM-DD.md` · `marketing/HOOKS.md`.
4. Optional: an Obsidian MCP server so the desktop Claude can search/edit the vault through tools. Since the vault is
   the repo, plain file access already works, so this is a "nice to have".

## Verdict
Worth 30 minutes to set up, as long as the vault is the repo folder. Start with Obsidian Git + Dataview; add the rest
only when we actually use them.
