from flask import Flask, request, jsonify
import requests
import time
import os

app = Flask(__name__)

API_KEY = os.getenv("INFOREGISTER_API_KEY")
BASE_URL = "https://api.ir.ee"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

PAGE_LIMIT = 100
REQUEST_DELAY = 0.2


def safe_get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2)


def get_companies_by_date(from_date, to_date, page):
    response = safe_get(
        f"{BASE_URL}/base_info_company_by_create_date/",
        {
            "created_from": from_date,
            "created_to": to_date,
            "page": page,
            "limit": PAGE_LIMIT
        }
    )
    return response.get("data", [])


def get_company_details(reg_code):
    return safe_get(
        f"{BASE_URL}/premium/company_contactsl/reg_code/{reg_code}"
    )


@app.route("/run", methods=["POST"])
def run():
    body = request.json

    from_date = body["from_date"]
    to_date = body["to_date"]
    target = body["target"]  # например 50 или 1000

    results = []
    page = 1

    while len(results) < target:
        companies = get_companies_by_date(from_date, to_date, page)
        if not companies:
            break

        for company in companies:
            if len(results) >= target:
                break

            reg_code = company.get("registry_code")
            if not reg_code:
                continue

            try:
                details = get_company_details(reg_code)
            except Exception:
                continue

            base_info = details.get("base_info", {})
            address = details.get("base_info_address", {})
            contact = details.get("base_info_contact", {})
            persons = details.get("base_info_persons", [])

            # фильтр: без VAT
            if base_info.get("kmkr"):
                continue

            person = persons[0] if persons else {}

            results.append({
                "reg_time": base_info.get("reg_time", ""),
                "company_name": base_info.get("company_name", ""),
                "vat_number": base_info.get("kmkr", ""),
                "full_address": address.get("full_address", ""),
                "email": contact.get("contact", ""),
                "beneficiary_country": person.get("country_code", ""),
                "beneficiary_personal_code": person.get("code", ""),
                "beneficiary_name": person.get("name", "")
            })

            time.sleep(REQUEST_DELAY)

        page += 1

    return jsonify({
        "count": len(results),
        "companies": results
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
