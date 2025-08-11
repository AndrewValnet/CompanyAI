#!/usr/bin/env python3
"""
similarweb_to_postgres.py

Submit a Similarweb Batch API report for the Websites "traffic_and_engagement" table,
wait for completion, download CSV, and load into PostgreSQL with simple upserts.

Usage:
  1) Copy .env.example to .env and fill in values
  2) pip install requests psycopg2-binary python-dotenv
  3) python similarweb_to_postgres.py

Notes:
- Uses "download_link" delivery method (no cloud setup required).
- Adjust metrics/countries/domains/date range to what your license allows.
"""

import csv
import io
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

BATCH_REQUEST_URL = "https://api.similarweb.com/batch/v4/request-report"
BATCH_QUERY_URL = "https://api.similarweb.com/v3/batch/request-query"  # expects ?report_id=...

# ---- Config helpers ----

@dataclass
class Settings:
    api_key: str
    pg_dsn: str
    domains: List[str]
    countries: List[str]
    start_date: str
    end_date: str
    metrics: List[str] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = [
                "all_traffic_visits",
                "all_traffic_pages_per_visit",
                "all_traffic_average_visit_duration",
                "all_traffic_bounce_rate",
                "all_page_views",
            ]


def load_settings() -> Settings:
    load_dotenv()
    api_key = os.getenv("SIMILARWEB_BATCH_API_KEY", "")
    if not api_key:
        raise SystemExit("Missing SIMILARWEB_BATCH_API_KEY in environment")

    pg_dsn = (
        f"host={os.getenv('PGHOST','127.0.0.1')} "
        f"port={os.getenv('PGPORT','5432')} "
        f"dbname={os.getenv('PGDATABASE','similarweb')} "
        f"user={os.getenv('PGUSER','postgres')} "
        f"password={os.getenv('PGPASSWORD','postgres')}"
    )

    domains = [d.strip() for d in os.getenv("DOMAINS", "example.com").split(",") if d.strip()]
    countries = [c.strip() for c in os.getenv("COUNTRIES", "WW").split(",") if c.strip()]
    start_date = os.getenv("START_DATE", "2024-01")
    end_date = os.getenv("END_DATE", "2024-12")
    return Settings(api_key, pg_dsn, domains, countries, start_date, end_date)


# ---- API ----

def submit_report(s: Settings) -> str:
    payload = {
        "delivery_information": {
            "response_format": "csv",
            "delivery_method": "download_link"
        },
        "report_query": {
            "tables": [
                {
                    "vtable": "traffic_and_engagement",
                    "granularity": "monthly",
                    "filters": {
                        "domains": s.domains,
                        "countries": s.countries,
                        "include_subdomains": True
                    },
                    "metrics": s.metrics,
                    "start_date": s.start_date,
                    "end_date": s.end_date
                }
            ]
        },
        "report_name": "sw_traffic_and_engagement"
    }
    headers = {
        "Content-Type": "application/json",
        "api-key": s.api_key   # Batch API uses 'api-key' header
    }
    r = requests.post(BATCH_REQUEST_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    report_id = data.get("report_id") or data.get("id") or data.get("reportId")
    if not report_id:
        raise RuntimeError(f"Could not parse report_id from response: {data}")
    return report_id


def wait_for_report(s: Settings, report_id: str, timeout_sec: int = 900, poll_every: int = 10) -> Dict[str, Any]:
    """
    Poll the request-query endpoint until status is 'completed' and a download link exists.
    """
    headers = {"api_key": s.api_key}
    deadline = time.time() + timeout_sec
    last = None
    while time.time() < deadline:
        r = requests.get(BATCH_QUERY_URL, params={"report_id": report_id}, headers=headers, timeout=30)
        if r.status_code == 404:
            # slight delay and retry
            time.sleep(poll_every)
            continue
        r.raise_for_status()
        last = r.json()

        status = (last.get("status") or last.get("report_status") or "").lower()
        download_link = last.get("download_link") or last.get("report_download_url") or None

        if download_link and status in ("completed", "success", "ready"):
            return {"download_link": download_link, "raw": last}

        # Sometimes the API returns a list of files; try to detect a link there
        files = last.get("files") or []
        if files and isinstance(files, list) and "url" in files[0]:
            return {"download_link": files[0]["url"], "raw": last}

        time.sleep(poll_every)

    raise TimeoutError(f"Report {report_id} not ready before timeout; last={last}")


def download_csv(url: str) -> str:
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    return r.text


# ---- Postgres ----

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS sw_traffic_engagement (
  domain              TEXT NOT NULL,
  country             TEXT NOT NULL,
  date                DATE NOT NULL,
  all_traffic_visits  DOUBLE PRECISION,
  all_traffic_pages_per_visit DOUBLE PRECISION,
  all_traffic_average_visit_duration DOUBLE PRECISION,
  all_traffic_bounce_rate DOUBLE PRECISION,
  all_page_views      DOUBLE PRECISION,
  load_ts             TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (domain, country, date)
);
"""

def parse_rows(csv_text: str) -> List[Dict[str, Any]]:
    buf = io.StringIO(csv_text)
    reader = csv.DictReader(buf)
    rows = []
    for row in reader:
        # Expecting columns like: domain,country,date,all_traffic_visits,...
        rows.append({
            "domain": row.get("domain") or row.get("Domain") or row.get("website") or "",
            "country": row.get("country") or row.get("Country") or row.get("geo") or "WW",
            "date": row.get("date") or row.get("Date"),
            "all_traffic_visits": row.get("all_traffic_visits"),
            "all_traffic_pages_per_visit": row.get("all_traffic_pages_per_visit"),
            "all_traffic_average_visit_duration": row.get("all_traffic_average_visit_duration"),
            "all_traffic_bounce_rate": row.get("all_traffic_bounce_rate"),
            "all_page_views": row.get("all_page_views"),
        })
    return rows


def upsert_rows(dsn: str, rows: List[Dict[str, Any]]):
    if not rows:
        print("No rows to load.")
        return

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_SQL)
            cols = [
                "domain","country","date",
                "all_traffic_visits","all_traffic_pages_per_visit",
                "all_traffic_average_visit_duration","all_traffic_bounce_rate",
                "all_page_views"
            ]
            values = [
                (
                    r["domain"],
                    r["country"],
                    r["date"],
                    _to_float(r["all_traffic_visits"]),
                    _to_float(r["all_traffic_pages_per_visit"]),
                    _to_float(r["all_traffic_average_visit_duration"]),
                    _to_float(r["all_traffic_bounce_rate"]),
                    _to_float(r["all_page_views"]),
                )
                for r in rows
            ]
            insert_sql = f"""
                INSERT INTO sw_traffic_engagement ({",".join(cols)})
                VALUES %s
                ON CONFLICT (domain, country, date) DO UPDATE SET
                  all_traffic_visits = EXCLUDED.all_traffic_visits,
                  all_traffic_pages_per_visit = EXCLUDED.all_traffic_pages_per_visit,
                  all_traffic_average_visit_duration = EXCLUDED.all_traffic_average_visit_duration,
                  all_traffic_bounce_rate = EXCLUDED.all_traffic_bounce_rate,
                  all_page_views = EXCLUDED.all_page_views,
                  load_ts = NOW();
            """
            execute_values(cur, insert_sql, values)
        conn.commit()


def _to_float(x: Optional[str]) -> Optional[float]:
    try:
        return float(x) if x not in (None, "", "null") else None
    except Exception:
        return None


def main():
    s = load_settings()
    print(f"Submitting report for {len(s.domains)} domains, countries={s.countries}, {s.start_date}..{s.end_date}")
    report_id = submit_report(s)
    print("Report ID:", report_id)

    print("Waiting for report to be ready...")
    result = wait_for_report(s, report_id)
    print("Download link:", result["download_link"])

    print("Downloading CSV...")
    csv_text = download_csv(result["download_link"])

    print("Parsing + loading into Postgres...")
    rows = parse_rows(csv_text)
    upsert_rows(s.pg_dsn, rows)
    print(f"Done. Loaded {len(rows)} rows into sw_traffic_engagement.")

if __name__ == "__main__":
    main()
