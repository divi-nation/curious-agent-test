#!/usr/bin/env python3
"""
Split journal.md into per-session files.
Run this from the root of your curious-agent-test repo.
It will create individual files in record/journal/ and rename the original to journal.md.bak.
Session numbers are zero‑padded to 3 digits (e.g., 1 → 001, 10 → 010).
Non‑numeric session numbers (e.g., 10B) are kept as‑is.
"""

import re
from pathlib import Path

JOURNAL_MD = Path("record/journal.md")
OUTPUT_DIR = Path("record/journal")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_entries(content):
    """Split content into entries based on timestamp lines."""
    timestamp_pattern = re.compile(r'^##\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', re.MULTILINE)
    entries = []
    lines = content.splitlines(keepends=True)
    current_entry = []
    for line in lines:
        if timestamp_pattern.match(line.strip()):
            if current_entry:
                entries.append(''.join(current_entry))
                current_entry = []
        current_entry.append(line)
    if current_entry:
        entries.append(''.join(current_entry))
    return entries


def extract_session_number(entry):
    """Extract session number from the header line (supports numbers and letters, e.g., 10B)."""
    match = re.search(r'=== Session ([A-Za-z0-9]+):', entry)
    if match:
        return match.group(1)
    return None


def extract_date(entry):
    """Extract date from the ## timestamp line."""
    match = re.search(r'^##\s+(\d{4}-\d{2}-\d{2})', entry, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def format_session_number(session_num):
    """
    Format the session number.
    If it's purely numeric, zero‑pad to 3 digits (e.g., 1 → 001, 10 → 010).
    Otherwise (e.g., 10B), keep as‑is.
    """
    if session_num is None:
        return "unknown"
    if session_num.isdigit():
        return f"{int(session_num):03d}"
    return session_num


def main():
    if not JOURNAL_MD.exists():
        print(f"❌ {JOURNAL_MD} not found. Are you in the repo root?")
        return

    print(f"📖 Reading {JOURNAL_MD}...")
    content = JOURNAL_MD.read_text(encoding="utf-8")
    entries = parse_entries(content)
    print(f"📝 Found {len(entries)} entries.")

    if not entries:
        print("⚠️ No entries found. Exiting.")
        return

    # Backup original
    backup = JOURNAL_MD.with_suffix(".md.bak")
    JOURNAL_MD.rename(backup)
    print(f"💾 Original backed up to {backup}")

    # Write each entry
    written = 0
    for entry in entries:
        raw_session = extract_session_number(entry)
        date = extract_date(entry)

        session = format_session_number(raw_session)
        if date is None:
            date = "unknown-date"

        filename = f"{date}-session-{session}.md"
        filepath = OUTPUT_DIR / filename

        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filename = f"{date}-session-{session}-{counter}.md"
            filepath = OUTPUT_DIR / filename
            counter += 1

        filepath.write_text(entry, encoding="utf-8")
        written += 1
        if written % 10 == 0:
            print(f"📝 Written {written} entries...")

    print(f"✅ Done. Created {written} files in {OUTPUT_DIR}/")
    print(f"📄 Original journal.md backed up to {backup}")


if __name__ == "__main__":
    main()