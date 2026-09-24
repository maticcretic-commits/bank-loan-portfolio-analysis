#!/usr/bin/env python3
"""Loan-portfolio health analysis (SYNTHETIC data — see generate_data.py).

Computes the asset-quality metrics a bank's credit/risk team watches:
  * Gross NPA ratio (NPA outstanding / total outstanding)
  * Delinquency distribution across SMA buckets
  * Branch-wise NPA performance
  * Vintage analysis — default rate by disbursement year
  * Risk segmentation (Low / Medium / High)

Charts are saved to charts/. Summary tables print to the console.

Run:  python3 analyze_portfolio.py   (needs pandas, matplotlib)
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("charts", exist_ok=True)
df = pd.read_csv("data/synthetic_loan_portfolio.csv",
                 parse_dates=["DisbursementDate"])
df["VintageYear"] = df["DisbursementDate"].dt.year
df["IsNPA"] = df["Status"] == "NPA"

# ------------------------------------------------- headline asset quality
total_os = df["OutstandingAmount"].sum()
npa_os = df.loc[df["IsNPA"], "OutstandingAmount"].sum()
gross_npa = npa_os / total_os
sma_os = df.loc[df["Status"].str.startswith("SMA"),
                "OutstandingAmount"].sum()

print(f"Loans analysed : {len(df):,}")
print(f"Total outstanding: Rs {total_os:,.0f}")
print(f"Gross NPA ratio  : {gross_npa:.2%}  (Rs {npa_os:,.0f})")
print(f"SMA (1-90 DPD)   : {sma_os / total_os:.2%} of outstanding")

# ------------------------------------------------- delinquency buckets
bucket = df.groupby("Status").agg(
    loans=("LoanID", "count"),
    outstanding=("OutstandingAmount", "sum")).reindex(
    ["Standard", "SMA-0", "SMA-1", "SMA-2", "NPA"])
bucket["pct_os"] = bucket["outstanding"] / total_os
print("\nDelinquency buckets:\n", bucket.round(2).to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(bucket.index, bucket["outstanding"] / 1e7, color="#1F4E78")
ax.set_title("Outstanding by delinquency bucket (Rs crore)")
ax.set_ylabel("Rs crore")
fig.tight_layout()
fig.savefig("charts/delinquency_buckets.png", dpi=120)
plt.close(fig)

# ------------------------------------------------- branch performance
branch = df.groupby("Branch").agg(
    loans=("LoanID", "count"),
    outstanding=("OutstandingAmount", "sum"),
    npa_os=("OutstandingAmount", lambda s: s[df.loc[s.index, "IsNPA"]].sum()),
)
branch["npa_pct"] = branch["npa_os"] / branch["outstanding"]
branch = branch.sort_values("npa_pct", ascending=False)
print("\nBranch-wise NPA%:\n", branch.round(2).to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(branch.index, branch["npa_pct"] * 100, color="#C0392B")
ax.set_title("Gross NPA % by branch (synthetic data)")
ax.set_xlabel("NPA % of branch outstanding")
fig.tight_layout()
fig.savefig("charts/npa_by_branch.png", dpi=120)
plt.close(fig)

# ------------------------------------------------- vintage analysis
vintage = df.groupby("VintageYear").agg(
    loans=("LoanID", "count"),
    npa_loans=("IsNPA", "sum"))
vintage["default_rate"] = vintage["npa_loans"] / vintage["loans"]
print("\nVintage default rates:\n", vintage.round(3).to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(vintage.index, vintage["default_rate"] * 100, marker="o",
        color="#1F4E78")
ax.set_title("Default rate by disbursement vintage (synthetic data)")
ax.set_xlabel("Disbursement year")
ax.set_ylabel("NPA % of loans disbursed")
fig.tight_layout()
fig.savefig("charts/vintage_default_rate.png", dpi=120)
plt.close(fig)

# ------------------------------------------------- risk segmentation
def segment(r):
    # Rule-based segmentation a risk team can audit and tune:
    # NPA or deep delinquency -> High; early stress or thin collateral -> Medium.
    if r["Status"] == "NPA" or r["Status"] == "SMA-2":
        return "High"
    if r["Status"].startswith("SMA"):
        return "Medium"
    if r["CollateralCoverage"] and r["CollateralCoverage"] < 0.8:
        return "Medium"  # standard loan, thin collateral cover
    return "Low"

df["RiskSegment"] = df.apply(segment, axis=1)
seg = pd.crosstab(df["LoanType"], df["RiskSegment"],
                  values=df["OutstandingAmount"], aggfunc="sum").fillna(0)
seg_pct = seg.div(seg.sum(axis=1), axis=0)
print("\nRisk segment share of outstanding by product:\n",
      seg_pct.round(3).to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
seg_pct[["Low", "Medium", "High"]].plot.barh(
    stacked=True, ax=ax, color=["#27AE60", "#F39C12", "#C0392B"])
ax.set_title("Risk segmentation by product (share of outstanding)")
ax.set_xlabel("Share")
fig.tight_layout()
fig.savefig("charts/risk_segmentation.png", dpi=120)
plt.close(fig)

print("\nCharts saved to charts/:",
      ", ".join(sorted(os.listdir("charts"))))
