#!/usr/bin/env python3
import requests, json, time, sys, os

# Your Batch API key
BATCH_API_KEY = "231fc369d4e44e51a46fce2df04cc61f"

# 1) Submit the report
submit_url = "https://api.similarweb.com/batch/v4/request-report"
payload = {
    "delivery_information": {
        "delivery_method": "download_link",
        "response_format": "csv"
    },
    "report_query": {
        "tables": [
            {
                "vtable": "traffic_and_engagement",
                "granularity": "monthly",
                "filters": {
                    "domains": ["google.com"],
                    "countries": ["US"],
                    "include_subdomains": True
                },
                "metrics": [
                    "all_traffic_visits",
                    "all_traffic_pages_per_visit",
                    "all_traffic_average_visit_duration",
                    "all_traffic_bounce_rate",
                    "all_page_views"
                ],
                "start_date": "2024-01",
                "end_date": "2024-03"
            }
        ]
    },
    "report_name": "google_traffic_and_engagement_test"
}
headers_submit = {
    "Content-Type": "application/json",
    "api-key": BATCH_API_KEY   # note: 'api-key' header name for submit
}

resp = requests.post(submit_url, headers=headers_submit, json=payload, timeout=60)
resp.raise_for_status()
resp_json = resp.json()
report_id = resp_json.get("report_id") or resp_json.get("id") or resp_json.get("reportId")
if not report_id:
    print("Could not find report_id in response:")
    print(json.dumps(resp_json, indent=2))
    sys.exit(1)

print("Report submitted. report_id =", report_id)

# 2) Poll for completion
query_url = "https://api.similarweb.com/v3/batch/request-query"
headers_query = {
    "api_key": BATCH_API_KEY    # note: 'api_key' header name for query
}
deadline = time.time() + 15 * 60   # up to 15 minutes
sleep_secs = 8

download_link = None
while time.time() < deadline:
    q = requests.get(query_url, params={"report_id": report_id}, headers=headers_query, timeout=30)
    if q.status_code == 404:
        # just submitted; give it a moment
        time.sleep(sleep_secs)
        continue
    q.raise_for_status()
    data = q.json()

    status = (data.get("status") or data.get("report_status") or "").lower()
    download_link = data.get("download_link") or data.get("report_download_url")

    # Some responses return a files[] list
    if not download_link and isinstance(data.get("files"), list) and data["files"]:
        download_link = data["files"][0].get("url")

    print("Status:", status or "unknown")

    if download_link and status in ("completed", "success", "ready"):
        break

    time.sleep(sleep_secs)

if not download_link:
    print("Timed out waiting for report to complete. Last response:")
    print(json.dumps(data, indent=2))
    sys.exit(1)

print("Report ready. Download link:", download_link)

# 3) Download CSV
csv_resp = requests.get(download_link, timeout=120)
csv_resp.raise_for_status()

out_name = "google_traffic_and_engagement_US_2024-01_2024-03.csv"
with open(out_name, "w", encoding="utf-8") as f:
    f.write(csv_resp.text)

print(f"Saved CSV -> {os.path.abspath(out_name)}")
