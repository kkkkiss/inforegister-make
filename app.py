import requests
import csv
import sys

API_KEY = input("Введи API ключ: ").strip()
BASE_URL = "https://api.ir.ee"
HEADERS = {"Authorization": API_KEY}

FROM_DATE = "2025-01-01"
TO_DATE = "2025-03-01"
LIMIT = 50

def get_companies_by_date():
    url = f"{BASE_URL}/base_info_company_by_create_date/reg_time/{FROM_DATE}/to/{TO_DATE}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()[:LIMIT]

def get_company_contacts(reg_code):
    url = f"{BASE_URL}/premium/company_contacts/reg_code/{reg_code}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()
    return {}

def extract_data(base_info, contacts):
    row = {
        "reg_code": base_info.get("reg_code", ""),
        "reg_time": base_info.get("reg_time", ""),
        "company_name": base_info.get("company_name", ""),
        "kmkr": base_info.get("kmkr", ""),
        "full_address": "",
        "email": "",
        "person_country": "",
        "person_code": "",
        "person_name": ""
    }
    
    # Address from base_info
    addr = base_info.get("base_info_address") or {}
    if isinstance(addr, list) and addr:
        addr = addr[0]
    row["full_address"] = addr.get("full_address", "") if isinstance(addr, dict) else ""
    
    # Email from contacts
    contact_list = contacts.get("base_info_contact") or []
    if isinstance(contact_list, list):
        for c in contact_list:
            if "@" in str(c.get("contact", "")):
                row["email"] = c.get("contact", "")
                break
    
    # Person info
    persons = base_info.get("base_info_persons") or []
    if isinstance(persons, list) and persons:
        p = persons[0]
        row["person_country"] = p.get("country_code", "")
        row["person_code"] = p.get("code", "")
        row["person_name"] = p.get("name", "")
    
    return row

def main():
    print(f"Загружаю компании за период {FROM_DATE} - {TO_DATE}...")
    
    companies = get_companies_by_date()
    print(f"Найдено {len(companies)} компаний")
    
    results = []
    for i, company in enumerate(companies):
        reg_code = company.get("reg_code", "")
        print(f"[{i+1}/{len(companies)}] {company.get('company_name', 'N/A')} ({reg_code})")
        
        contacts = get_company_contacts(reg_code) if reg_code else {}
        row = extract_data(company, contacts)
        results.append(row)
    
    # Save to CSV
    output_file = "companies_estonia.csv"
    fieldnames = ["reg_code", "reg_time", "company_name", "kmkr", "full_address", "email", "person_country", "person_code", "person_name"]
    
    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nГотово! Сохранено в {output_file}")

if __name__ == "__main__":
    main()
