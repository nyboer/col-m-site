#!/usr/bin/env python3
"""
col-m.us site builder
Downloads public Google Drive files listed in files.txt, rebuilds index.html
"""

import re
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT  = Path(__file__).parent.parent
IMAGES_DIR = REPO_ROOT / "images"
TEMPLATE   = REPO_ROOT / "template" / "index.template.html"
OUTPUT     = REPO_ROOT / "index.html"
FILES_LIST = REPO_ROOT / "files.txt"


# ── Google Drive download ─────────────────────────────────────────────────────

def drive_url(file_id):
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def download_file(file_id, dest_path):
    url = drive_url(file_id)
    print(f"  Downloading {dest_path.name} ...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest_path)
        print("✓")
    except urllib.error.URLError as e:
        print(f"✗  FAILED: {e}")
        raise


# ── files.txt parser ──────────────────────────────────────────────────────────

def parse_files_list(text):
    """
    Parse files.txt — one entry per line:
        filename    DRIVE_FILE_ID
    Blank lines and lines starting with # are ignored.
    """
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            print(f"  Skipping malformed line: {line!r}")
            continue
        entries.append((parts[0], parts[1]))
    return entries


# ── Markdown parser ───────────────────────────────────────────────────────────

def parse_events_md(md_text):
    """
    Parse events.md into a list of event dicts.

    Format per event (separate blocks with ---):

        ## Month YYYY — Venue Name
        **Date:** Saturday, January 18, 2025
        **Artists:** Artist One, Artist Two
        **Doors:** 8pm | **Show:** 9pm | **Cover:** $10
        **Poster:** poster-jan-2025.jpg

        Optional freeform description paragraph.
    """
    events = []
    blocks = re.split(r"\n---+\n", md_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        event = {}

        title_match = re.search(r"^##\s+(.+)$", block, re.MULTILINE)
        event["title"] = title_match.group(1).strip() if title_match else ""
        if not event["title"]:
            continue

        for key, field in [
            ("date",    "Date"),
            ("artists", "Artists"),
            ("details", "Doors"),
            ("poster",  "Poster"),
        ]:
            m = re.search(rf"\*\*{field}:\*\*\s*(.+)", block)
            event[key] = m.group(1).strip() if m else ""

        desc_lines = []
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or re.match(r"\*\*\w[\w\s]*:\*\*", line):
                continue
            desc_lines.append(line)
        event["description"] = " ".join(desc_lines)

        events.append(event)

    return events


# ── HTML builder ──────────────────────────────────────────────────────────────

def build_event_html(event):
    poster_file = event.get("poster", "").strip()
    img_tag = (
        f'<img src="images/{poster_file}" alt="{event["title"]} poster" class="poster">'
        if poster_file
        else '<div class="poster poster--placeholder"></div>'
    )

    artists_html = ""
    if event.get("artists"):
        artists = [a.strip() for a in event["artists"].split(",")]
        artists_html = (
            '<ul class="artists">'
            + "".join(f"<li>{a}</li>" for a in artists)
            + "</ul>"
        )

    desc_html = (
        f'<p class="description">{event["description"]}</p>'
        if event.get("description")
        else ""
    )

    return f"""
    <article class="event">
      <div class="event__poster">
        {img_tag}
      </div>
      <div class="event__info">
        <h2 class="event__title">{event["title"]}</h2>
        <p class="event__date">{event.get("date", "")}</p>
        {artists_html}
        <p class="event__details">{event.get("details", "")}</p>
        {desc_html}
      </div>
    </article>"""


def render_html(template_text, events):
    events_html = "\n".join(build_event_html(e) for e in events)
    updated = datetime.now().strftime("%B %d, %Y")
    return (
        template_text
        .replace("{{ EVENTS }}", events_html)
        .replace("{{ UPDATED }}", updated)
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("🎵 col-m.us builder starting...")

    if not FILES_LIST.exists():
        raise FileNotFoundError(
            "files.txt not found in repo root. "
            "Add one listing your Drive file IDs."
        )

    entries = parse_files_list(FILES_LIST.read_text())
    print(f"Found {len(entries)} file(s) in files.txt.")

    # Clear and recreate images dir
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    IMAGES_DIR.mkdir()

    events_md_text = None

    for filename, file_id in entries:
        if filename.endswith(".md"):
            tmp = REPO_ROOT / filename
            download_file(file_id, tmp)
            events_md_text = tmp.read_text(encoding="utf-8")
            tmp.unlink()
        else:
            download_file(file_id, IMAGES_DIR / filename)

    if not events_md_text:
        raise ValueError(
            "No .md file found in files.txt. "
            "Make sure events.md is listed there."
        )

    events = parse_events_md(events_md_text)
    print(f"Parsed {len(events)} event(s).")

    template_text = TEMPLATE.read_text(encoding="utf-8")
    html = render_html(template_text, events)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"✅ Built index.html with {len(events)} event(s).")


if __name__ == "__main__":
    main()
