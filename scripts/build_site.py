#!/usr/bin/env python3
"""
col-m.us site builder
Fetches poster images + events.md from Google Drive, rebuilds index.html
"""

import os
import io
import re
import json
import shutil
from pathlib import Path
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# ── Config ────────────────────────────────────────────────────────────────────

# Set DRIVE_FOLDER_ID in your GitHub Actions secrets (or .env for local use)
DRIVE_FOLDER_ID = os.environ["DRIVE_FOLDER_ID"]

# The service account JSON is stored as a GitHub secret (GOOGLE_SERVICE_ACCOUNT_JSON)
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

REPO_ROOT = Path(__file__).parent.parent
IMAGES_DIR = REPO_ROOT / "images"
TEMPLATE_PATH = REPO_ROOT / "template" / "index.template.html"
OUTPUT_PATH = REPO_ROOT / "index.html"


# ── Google Drive helpers ───────────────────────────────────────────────────────

def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_INFO, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def list_drive_files(service, folder_id):
    """Return list of {id, name, mimeType} dicts in the folder."""
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        orderBy="name desc"
    ).execute()
    return results.get("files", [])


def download_file(service, file_id, dest_path):
    request = service.files().get_media(fileId=file_id)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    print(f"  Downloaded → {dest_path.name}")


# ── Markdown parser ────────────────────────────────────────────────────────────

def parse_events_md(md_text):
    """
    Parse events.md into a list of event dicts.

    Expected format per event (repeat for each event, separated by ---):

        ## Month YYYY — Venue Name
        **Date:** Saturday, January 18, 2025
        **Artists:** Artist One, Artist Two
        **Doors:** 8pm | **Show:** 9pm | **Cover:** $10
        **Poster:** poster-jan-2025.jpg

        Optional freeform description paragraph(s) here.

    """
    events = []
    # Split on horizontal rules
    blocks = re.split(r"\n---+\n", md_text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        event = {}

        # Title from ## heading
        title_match = re.search(r"^##\s+(.+)$", block, re.MULTILINE)
        event["title"] = title_match.group(1).strip() if title_match else ""

        # Labeled fields: **Key:** Value
        for key, field in [
            ("date", "Date"),
            ("artists", "Artists"),
            ("details", "Doors"),
            ("poster", "Poster"),
        ]:
            match = re.search(rf"\*\*{field}:\*\*\s*(.+)", block)
            event[key] = match.group(1).strip() if match else ""

        # Freeform description: lines that aren't headings or **Key:** lines
        desc_lines = []
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if re.match(r"\*\*\w[\w\s]*:\*\*", line):
                continue
            desc_lines.append(line)
        event["description"] = " ".join(desc_lines)

        events.append(event)

    return events


# ── HTML builder ───────────────────────────────────────────────────────────────

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
        artists_html = '<ul class="artists">' + "".join(
            f"<li>{a}</li>" for a in artists
        ) + "</ul>"

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
    html = template_text
    html = html.replace("{{ EVENTS }}", events_html)
    html = html.replace("{{ UPDATED }}", updated)
    return html


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("🎵 col-m.us builder starting...")

    service = get_drive_service()
    files = list_drive_files(service, DRIVE_FOLDER_ID)
    print(f"Found {len(files)} file(s) in Drive folder.")

    # Clear and recreate images dir
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    IMAGES_DIR.mkdir()

    events_md_text = None

    for f in files:
        name = f["name"]
        mime = f["mimeType"]

        if name == "events.md" or (name.endswith(".md") and "event" in name.lower()):
            # Download markdown to memory
            request = service.files().get_media(fileId=f["id"])
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            events_md_text = buf.getvalue().decode("utf-8")
            print(f"  Read events file: {name}")

        elif mime.startswith("image/") or name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            download_file(service, f["id"], IMAGES_DIR / name)

    if not events_md_text:
        raise FileNotFoundError(
            "No events.md found in the Drive folder. "
            "Make sure a file named 'events.md' exists there."
        )

    events = parse_events_md(events_md_text)
    print(f"Parsed {len(events)} event(s).")

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = render_html(template_text, events)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"✅ Built index.html with {len(events)} event(s).")


if __name__ == "__main__":
    main()
