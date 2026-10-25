"""Rule-based extraction of basic fields from offer text (baseline v0)."""
import re
import sys
from pathlib import Path

import pandas as pd

# Longest names first, so "Jakarta Pusat" wins over "Jakarta"
CITIES = [
    "Jakarta Pusat", "Jakarta Selatan", "Jakarta Barat", "Jakarta Utara",
    "Jakarta Timur", "Jakarta", "Bandung", "Cimahi", "Bekasi", "Depok",
    "Tangerang", "Bogor", "Surabaya", "Yogyakarta", "Semarang", "Malang",
    "Medan", "Denpasar", "Bali",
]
CITY_RE = re.compile(r"\b(" + "|".join(CITIES) + r")\b", re.IGNORECASE)

MONTHS = {
    "january": 1, "januari": 1, "jan": 1, "february": 2, "februari": 2, "feb": 2,
    "march": 3, "maret": 3, "mar": 3, "april": 4, "apr": 4, "may": 5, "mei": 5,
    "june": 6, "juni": 6, "jun": 6, "july": 7, "juli": 7, "jul": 7,
    "august": 8, "agustus": 8, "aug": 8, "agu": 8, "september": 9, "sep": 9,
    "sept": 9, "october": 10, "oktober": 10, "oct": 10, "okt": 10,
    "november": 11, "nov": 11, "december": 12, "desember": 12, "dec": 12, "des": 12,
}
DEADLINE_WORDS = re.compile(
    r"deadline|batas|closing|ditutup|sampai|hingga|until|before|paling lambat",
    re.IGNORECASE,
)
ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
DMY = re.compile(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})")
MDY = re.compile(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})")


def find_location(text: str) -> str:
    match = CITY_RE.search(text)  # earliest city mentioned
    if match:
        return match.group(1).title()
    return "Indonesia" if re.search(r"\bIndonesia\b", text, re.IGNORECASE) else ""


def find_work_mode(text: str) -> str:
    t = text.lower()
    if re.search(r"\bhybrid\b", t):
        return "hybrid"
    if re.search(r"\b(remote|wfh|work from home)\b", t):
        return "remote"
    if re.search(r"\b(on-?site|wfo|work from office)\b", t):
        return "onsite"
    return ""


def find_deadline(text: str) -> str:
    """Return YYYY-MM-DD from a line that mentions a deadline word, else ''."""
    for line in text.splitlines():
        if not DEADLINE_WORDS.search(line):
            continue
        m = ISO.search(line)
        if m:
            return f"{m[1]}-{m[2]}-{m[3]}"
        m = DMY.search(line)
        if m and m[2].lower() in MONTHS:
            return f"{int(m[3]):04d}-{MONTHS[m[2].lower()]:02d}-{int(m[1]):02d}"
        m = MDY.search(line)
        if m and m[1].lower() in MONTHS:
            return f"{int(m[3]):04d}-{MONTHS[m[1].lower()]:02d}-{int(m[2]):02d}"
    return ""


def extract(text: str) -> dict:
    return {
        "location": find_location(text),
        "work_mode": find_work_mode(text),
        "deadline": find_deadline(text),
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    truth = pd.read_csv("data/labeled/ground_truth.csv", dtype=str).fillna("")
    truth = truth.set_index("id")

    for path in sorted(Path("data/samples").glob("web_*.txt")):
        offer_id = path.stem
        if offer_id not in truth.index:
            continue
        pred = extract(path.read_text(encoding="utf-8"))
        print(f"\n{offer_id}")
        for field, value in pred.items():
            expected = truth.loc[offer_id, field]
            status = "OK " if value.lower() == expected.lower() else "BAD"
            print(f"  {status} {field}: predicted={value!r} expected={expected!r}")
