#!/usr/bin/env python3
"""Clear matches and seed FIFA World Cup 2026 group stage + Round of 16 fixtures."""

import json
import sys
from pathlib import Path

import requests

SUPABASE_URL = "https://dhxboqlewvfmpovknvzs.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_SECRET_KEY"
MATCHES_URL = f"{SUPABASE_URL}/rest/v1/matches"
PREDICTIONS_URL = f"{SUPABASE_URL}/rest/v1/predictions"
DATA_FILE = Path(__file__).parent / "wc2026_matches.json"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def request(method, url, **kwargs):
    r = requests.request(method, url, headers=HEADERS, timeout=60, **kwargs)
    if not r.ok:
        raise RuntimeError(f"{method} {url} failed ({r.status_code}): {r.text}")
    return r


def clear_table(url):
    request("DELETE", f"{url}?id=gt.0")


def insert_matches(rows):
    batch_size = 50
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        request("POST", MATCHES_URL, json=batch)


def main():
    if not DATA_FILE.is_file():
        print(f"Missing {DATA_FILE}. Regenerate with the parser in project docs.", file=sys.stderr)
        sys.exit(1)

    rows = json.loads(DATA_FILE.read_text())
    print(f"Loaded {len(rows)} matches from {DATA_FILE.name}")

    print("Deleting predictions…")
    clear_table(PREDICTIONS_URL)

    print("Deleting matches…")
    clear_table(MATCHES_URL)

    print("Inserting World Cup fixtures…")
    insert_matches(rows)

    print(f"Done — inserted {len(rows)} matches (72 group stage + 8 Round of 16).")


if __name__ == "__main__":
    main()
