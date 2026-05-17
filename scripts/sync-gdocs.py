#!/usr/bin/env python3
"""
sync-gdocs.py
Fetches a Google Doc (shared with "anyone with the link") and writes data/sessions.json

Usage:
  python3 scripts/sync-gdocs.py <GOOGLE_DOC_ID>
  OR set GOOGLE_DOC_ID in .env and run without arguments

The doc must be shared as "anyone with the link can view".
Find the doc ID in the URL: docs.google.com/document/d/THIS_PART/edit
"""

import sys
import os
import re
import json
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

# Load .env if it exists
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

doc_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GOOGLE_DOC_ID", "")
if not doc_id:
    print("❌ No GOOGLE_DOC_ID provided.")
    print("   Usage: python3 scripts/sync-gdocs.py <DOC_ID>")
    print("   Or set GOOGLE_DOC_ID in .env")
    sys.exit(1)

# Fetch doc as plain text (works for docs shared with "anyone with link")
url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
print(f"⟳ Fetching Google Doc: {doc_id[:20]}...")

try:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", errors="replace")
except URLError as e:
    print(f"❌ Failed to fetch doc: {e}")
    print("   Make sure the doc is shared as 'Anyone with the link can view'")
    sys.exit(1)

# Parse sessions from text
# Expects headers like "Sesión 1 — Título" or "Session 1: Title"
lines = text.splitlines()
sessions = []
current = None

SESSION_HEADER = re.compile(
    r'^(Sesi[oó]n\s+\d+|Session\s+\d+|SESI[OÓ]N\s+\d+)',
    re.IGNORECASE
)
DATE_PATTERN = re.compile(
    r'\d{1,2}\s+de\s+\w+|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}',
    re.IGNORECASE
)

for line in lines:
    stripped = line.strip()
    if not stripped:
        continue
    if SESSION_HEADER.match(stripped):
        if current:
            sessions.append(current)
        current = {"title": stripped, "date": None, "content": []}
    elif current:
        if not current["date"]:
            m = DATE_PATTERN.search(stripped)
            if m:
                current["date"] = m.group(0)
        current["content"].append(stripped)

if current:
    sessions.append(current)

# If no session headers found, treat whole doc as single entry
if not sessions and lines:
    non_empty = [l.strip() for l in lines if l.strip()]
    sessions = [{"title": "Historial de campaña", "date": None, "content": non_empty}]

output = {
    "docId": doc_id,
    "lastSynced": datetime.now().isoformat(),
    "sessions": sessions,
}

output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sessions.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Synced {len(sessions)} session(s) → {output_path}")
for i, s in enumerate(sessions, 1):
    date_str = f" ({s['date']})" if s.get('date') else ""
    print(f"   {i}. {s['title']}{date_str} — {len(s['content'])} paragraphs")
