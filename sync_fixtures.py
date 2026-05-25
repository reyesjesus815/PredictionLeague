#!/usr/bin/env python3
"""Fetch Premier League fixtures and save them to Supabase (HTTP only, no SDK)."""

import os
import sys

import requests

FOOTBALL_DATA_URL = "https://api.football-data.org/v4/competitions/PL/matches"
SUPABASE_MATCHES_URL = "https://dhxboqlewvfmpovknvzs.supabase.co/rest/v1/matches"
SUPABASE_KEY = "YOUR_SUPABASE_SECRET_KEY"

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def load_env(path=".env"):
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def map_status(status):
    s = (status or "").upper()
    if s in ("SCHEDULED", "TIMED", "POSTPONED"):
        return "upcoming"
    if s in ("IN_PLAY", "PAUSED", "SUSPENDED"):
        return "live"
    if s == "FINISHED":
        return "finished"
    if s == "CANCELLED":
        return "cancelled"
    return "upcoming"


def to_row(match):
    full_time = (match.get("score") or {}).get("fullTime") or {}
    return {
        "home_team": (match.get("homeTeam") or {}).get("name", "").strip(),
        "away_team": (match.get("awayTeam") or {}).get("name", "").strip(),
        "competition": "Premier League",
        "match_date": match.get("utcDate"),
        "home_score": full_time.get("home"),
        "away_score": full_time.get("away"),
        "status": map_status(match.get("status")),
    }


def find_existing_id(row):
    params = {
        "select": "id",
        "home_team": f"eq.{row['home_team']}",
        "away_team": f"eq.{row['away_team']}",
        "limit": "1",
    }
    if row["match_date"]:
        params["match_date"] = f"eq.{row['match_date']}"
    else:
        params["match_date"] = "is.null"

    r = requests.get(
        SUPABASE_MATCHES_URL,
        headers=SUPABASE_HEADERS,
        params=params,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase lookup failed ({r.status_code}): {r.text}")

    data = r.json()
    return data[0]["id"] if data else None


def save_row(row):
    existing_id = find_existing_id(row)

    if existing_id is not None:
        r = requests.patch(
            SUPABASE_MATCHES_URL,
            headers=SUPABASE_HEADERS,
            params={"id": f"eq.{existing_id}"},
            json=row,
            timeout=30,
        )
        if not r.ok:
            raise RuntimeError(f"Supabase update failed ({r.status_code}): {r.text}")
        return "updated"

    r = requests.post(
        SUPABASE_MATCHES_URL,
        headers=SUPABASE_HEADERS,
        json=row,
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase insert failed ({r.status_code}): {r.text}")
    return "inserted"


def main():
    load_env()
    football_key = os.environ.get("FOOTBALL_DATA_API_KEY")
    if not football_key:
        print("Set FOOTBALL_DATA_API_KEY in .env", file=sys.stderr)
        sys.exit(1)

    r = requests.get(
        FOOTBALL_DATA_URL,
        headers={"X-Auth-Token": football_key},
        timeout=30,
    )
    r.raise_for_status()
    matches = r.json().get("matches") or []

    inserted = updated = errors = 0
    for match in matches:
        row = to_row(match)
        try:
            if save_row(row) == "inserted":
                inserted += 1
            else:
                updated += 1
        except Exception as exc:
            errors += 1
            print(f"Failed {row['home_team']} vs {row['away_team']}: {exc}", file=sys.stderr)

    print(f"Done: {len(matches)} fixtures — {inserted} inserted, {updated} updated, {errors} errors.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
