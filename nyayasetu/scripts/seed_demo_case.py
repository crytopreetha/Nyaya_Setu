"""
Creates and analyzes one demo case against a running API, for a quick sanity
check without opening the frontend.

Usage: python scripts/seed_demo_case.py [API_BASE_URL]
"""
import sys
import time

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

SAMPLE_NOTICE = """
Notice to Vacate

You are hereby informed that the tenancy for the above premises stands
terminated. You are required to respond in writing within 15 days of
receipt of this notice, and to vacate the premises by 30/11/2026. Please
note that the security deposit will be adjusted against damages and wear
and tear as assessed by the landlord.
"""


def main():
    with httpx.Client(base_url=BASE_URL, timeout=30) as client:
        resp = client.post(
            "/api/cases",
            json={
                "domain": "rental_tenancy",
                "input_type": "text",
                "text_input": SAMPLE_NOTICE,
                "consent": True,
            },
        )
        resp.raise_for_status()
        case = resp.json()
        case_id = case["id"]
        print(f"Created case {case_id}")

        client.post(f"/api/cases/{case_id}/analyze")

        for _ in range(30):
            status = client.get(f"/api/cases/{case_id}/status").json()
            print("status:", status["status"])
            if status["status"] in ("ready", "failed"):
                break
            time.sleep(1)

        analysis = client.get(f"/api/cases/{case_id}/analysis").json()
        print("\n--- Analysis ---")
        for item in analysis["risk_items"]:
            print(f"[{item['severity']}] {item['title']}: {item['explanation'][:100]}...")
        for d in analysis["important_dates"]:
            print(f"Deadline: {d['label']} -> {d['date']} ({d['confidence']})")


if __name__ == "__main__":
    main()
