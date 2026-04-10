#!/usr/bin/env python3
"""
col-m.us site builder
Reads files.txt, downloads event .txt files + images from public Google Drive,
rebuilds index.html from the template.
"""

import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
IMAGES_DIR = REPO_ROOT / "images"
TEMPLATE = REPO_ROOT / "template" / "index.template.html"
OUTPUT = REPO_ROOT / "index.html"
FILES_LIST = REPO_ROOT / "files.txt"


# ── Google Drive download ─────────────────────────────────────────────────────


def file_id_from_url(url):
    """Extract a Drive file ID from a share URL, or return the string as-is."""
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    print(f"✗  ID: {m.group(1)}")
    return m.group(1) if m else url.strip()


def drive_download_url(file_id):
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def download_file(file_id, dest_path):
    url = drive_download_url(file_id)
    print(f"  Downloading {file_id} {dest_path.name} ...", end=" ", flush=True)
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
        filename    DRIVE_URL_OR_FILE_ID
    The second column can be a full Google Drive share URL or just a bare ID.
    Blank lines and lines starting with # are ignored.
    Order is preserved; that's the display order of events.
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
        filename = parts[0]
        file_id = file_id_from_url(parts[1])
        entries.append((filename, file_id))
    return entries


# ── Event .txt parser ─────────────────────────────────────────────────────────


def parse_event_txt(text, image_filename):
    """
    Parse a single event .txt file.

    Format — four sections separated by blank lines:

        Title of the Event

        Date string

        Description line one.
        Description line two.

        https://drive.google.com/file/d/FILE_ID/view

    The image link in the .txt is ignored if an image filename is already
    known from files.txt (which takes precedence).
    """
    # Split into paragraphs on blank lines
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text.strip())]

    event = {
        "title": paragraphs[0] if len(paragraphs) > 0 else "",
        "date": paragraphs[1] if len(paragraphs) > 1 else "",
        "description": paragraphs[2] if len(paragraphs) > 2 else "",
        "image_filename": image_filename,
    }

    return event


# ── HTML builder ──────────────────────────────────────────────────────────────


def build_event_html(event):
    img_filename = event.get("image_filename", "")
    img_tag = (
        f'<img src="images/{img_filename}" alt="{event["title"]} poster" class="poster">'
        if img_filename
        else '<div class="poster poster--placeholder"></div>'
    )

    # Preserve line breaks in description
    desc_html = ""
    if event.get("description"):
        lines = event["description"].splitlines()
        desc_html = '<p class="description">' + "<br>".join(lines) + "</p>"

    return f"""
    <article class="event">
      <div class="event__poster">
        {img_tag}
      </div>
      <div class="event__info">
        <h2 class="event__title">{event["title"]}</h2>
        <p class="event__date">{event["date"]}</p>
        {desc_html}
      </div>
    </article>"""


def render_html(template_text, events):
    events_html = "\n".join(build_event_html(e) for e in events)
    updated = datetime.now().strftime("%B %d, %Y")
    return template_text.replace("{{ EVENTS }}", events_html).replace(
        "{{ UPDATED }}", updated
    )


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("🎵 col-m.us builder starting...")

    if not FILES_LIST.exists():
        raise FileNotFoundError("files.txt not found in repo root.")

    entries = parse_files_list(FILES_LIST.read_text())
    print(f"Found {len(entries)} file(s) in files.txt.")

    # Clear and recreate images dir
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    IMAGES_DIR.mkdir()

    # Group entries: pair each .txt with the next image file
    # Build a lookup: txt filename → image filename (from the adjacent image entry)
    txt_files = []  # [(local_name, file_id)]
    img_files = []  # [(local_name, file_id)]

    for filename, file_id in entries:
        if filename.endswith(".txt"):
            txt_files.append((filename, file_id))
        else:
            img_files.append((filename, file_id))

    # Download all images
    for img_name, file_id in img_files:
        download_file(file_id, IMAGES_DIR / img_name)

    # Download all .txt files, parse each one
    # Match txt to image by position (first txt → first image, etc.)
    events = []
    for i, (txt_name, file_id) in enumerate(txt_files):
        tmp = REPO_ROOT / txt_name
        download_file(file_id, tmp)
        txt_content = tmp.read_text(encoding="utf-8")
        tmp.unlink()

        # Find the corresponding image filename by position
        img_filename = img_files[i][0] if i < len(img_files) else ""
        event = parse_event_txt(txt_content, img_filename)
        events.append(event)
        print(f"  Parsed: {event['title']}")

    print(f"Total: {len(events)} event(s).")

    template_text = TEMPLATE.read_text(encoding="utf-8")
    html = render_html(template_text, events)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"✅ Built index.html.")


if __name__ == "__main__":
    main()
