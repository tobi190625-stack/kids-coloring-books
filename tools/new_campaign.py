#!/usr/bin/env python3
"""Start a campaign folder for a book: campaigns/<slug>/CAMPAIGN.md filled from campaigns/_TEMPLATE.

Usage: python3 tools/new_campaign.py books/005-rocco-monster-truck [AMAZON_LINK]
Then make the ad files (pins, carousels, videos) into the same folder and fill the video table.
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(book_dir, link=None):
    book_dir = Path(book_dir)
    book = json.loads((book_dir / "book.json").read_text())
    m = book.get("marketing", {})
    slug = m.get("slug") or book_dir.name.split("-")[1]
    title = book["title"].replace("’", "'")
    out = ROOT / "campaigns" / slug
    out.mkdir(parents=True, exist_ok=True)
    target = out / "CAMPAIGN.md"
    if target.exists():
        sys.exit(f"{target} already exists, not overwriting")
    hook = m.get("hook", "A coloring book that teaches reading.")
    fill = {
        "TITLE": title,
        "STATUS": "LIVE" if link else "waiting for KDP",
        "LINK": link or "(add the amazon.com/dp/... link when live)",
        "BOOK_DIR": str(book_dir),
        "SEASON": m.get("season", "all year"),
        "DATE": datetime.date.today().isoformat(),
        "HOOK1": hook,
        "SHORT_TITLE": m.get("short_title", f"Watch this page come to life: {title}"),
        "PIN1": m.get("pin_title", f"Coloring book for kids ages 3-6: {title}"),
    }
    text = (ROOT / "campaigns" / "_TEMPLATE" / "CAMPAIGN.md").read_text()
    for k, v in fill.items():
        text = text.replace("{{" + k + "}}", v)
    target.write_text(text)
    print("✓", target)


if __name__ == "__main__":
    main(*sys.argv[1:3])
