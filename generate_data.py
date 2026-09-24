#!/usr/bin/env python3
"""Generate synthetic_loan_portfolio.csv — 2000 synthetic loan records.

All data is FAKE and generated for demonstration purposes only.
It does not come from any real bank, customer, or portfolio.

Run: python3 generate_data.py   (writes data/synthetic_loan_portfolio.csv)
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(7)
os.makedirs("data", exist_ok=True)

BRANCHES = ["Patna Main", "Boring Road", "Kankarbagh", "Danapur",
            "Hajipur", "Muzaffarpur", "Gaya", "Bhagalpur"]
LOAN_TYPES = {
    "Home":     (800_000, 3_000_000, 8.5, 1.4),
    "Auto":     (300_000, 1_200_000, 10.5, 1.1),
    "Personal": (50_000,   500_000, 13.5, 0.0),
    "Business": (500_000, 5_000_000, 11.5, 1.2),
    "Agri":     (100_000,   800_000,  7.5, 1.0),
}
# base default propensity per loan type (shapes the DPD draw)
DEFAULT_RISK = {"Home": 0.04, "Auto": 0.08, "Personal": 0.16,
                "Business": 0.12, "Agri": 0.10}

FIRST = date(2019, 1, 1)
SPAN = (date(2025, 6, 30) - FIRST).days
N = 2000


def draw_dpd(loan_type):
    """DPD skewed to 0 with a fat tail; riskier products go bad more often."""
    r = random.random()
    risk = DEFAULT_RISK[loan_type]
    if r > risk:
        return 0
    # delinquent: pick a bucket
    b = random.random()
    if b < 0.35:
        return random.randint(1, 30)
    if b < 0.60:
        return random.randint(31, 60)
    if b < 0.78:
        return random.randint(61, 90)
    return random.randint(91, 540)


def status(dpd):
    if dpd == 0:
        return "Standard"
    if dpd <= 30:
        return "SMA-0"
    if dpd <= 60:
        return "SMA-1"
    if dpd <= 90:
        return "SMA-2"
    return "NPA"


with open("data/synthetic_loan_portfolio.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["LoanID", "Branch", "DisbursementDate", "LoanType",
                "SanctionedAmount", "OutstandingAmount", "DPD",
                "InterestRate", "CollateralCoverage", "Status"])
    for i in range(N):
        lt = random.choices(list(LOAN_TYPES),
                            weights=[30, 20, 25, 15, 10])[0]
        lo, hi, rate, cov = LOAN_TYPES[lt]
        sanctioned = random.randint(lo, hi)
        dpd = draw_dpd(lt)
        # older / stressed loans have higher outstanding relative to sanctioned
        outstanding = round(sanctioned * random.uniform(0.35, 0.95))
        disb = FIRST + timedelta(days=random.randint(0, SPAN))
        coverage = round(cov * random.uniform(0.85, 1.15), 2) if cov else 0.0
        w.writerow([f"LN-{100001 + i}", random.choice(BRANCHES),
                    disb.isoformat(), lt, sanctioned, outstanding, dpd,
                    round(rate + random.uniform(-0.5, 1.5), 2),
                    coverage, status(dpd)])

print("Wrote data/synthetic_loan_portfolio.csv")
