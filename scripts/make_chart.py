"""make_chart.py - before/after chart for the README (images/raw_vs_clean.png)."""
import csv
import datetime as dt
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "output", "weekly_compare.csv"))))
weeks = [dt.date.fromisoformat(r["week_ending"]) for r in rows]
raw = [float(r["raw_cases"]) for r in rows]
clean = [float(r["clean_cases"]) for r in rows]
raw_st = [int(r["raw_store_count"]) for r in rows]
clean_st = [int(r["clean_store_count"]) for r in rows]
cut = next(w for w, r in zip(weeks, rows) if r["territory_owner"] == "NEW")
ov = [w for w, r in zip(weeks, rows) if r["is_overlap_week"] == "1"]
gap = [w for w, r in zip(weeks, rows) if r["is_estimated_week"] == "1"]

RED, NAVY, GREY = "#DB0A40", "#1E2A4A", "#9AA0A6"
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
fig.suptitle("Territory switch: raw distributor data vs. cleaned history (simulated data)",
             fontsize=13, fontweight="bold", x=0.01, ha="left")

a1.plot(weeks, raw, color=RED, lw=1.8, label="Raw (both files loaded as-is)")
a1.plot(weeks, clean, color=NAVY, lw=2.4, label="Cleaned")
a1.scatter(gap, [clean[weeks.index(g)] for g in gap], color=NAVY, zorder=5, s=40, facecolor="white", lw=2,
           label="Estimated week")
for w in ov:
    a1.annotate("Overlap week:\nboth distributors reported", xy=(w, raw[weeks.index(w)]),
                xytext=(-170, -5), textcoords="offset points", fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))
for w in gap:
    a1.annotate("Missing file:\nsales look like zero", xy=(w, raw[weeks.index(w)]),
                xytext=(25, 20), textcoords="offset points", fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))
a1.set_ylabel("Cases per week")
a1.set_ylim(0, max(raw) * 1.12)
a1.legend(loc="lower left", frameon=False, fontsize=9)

a2.plot(weeks, raw_st, color=RED, lw=1.8, label="Raw store count")
a2.plot(weeks, clean_st, color=NAVY, lw=2.4, label="Cleaned store count")
a2.set_ylabel("Stores selling")
a2.set_ylim(0, max(raw_st) * 1.15)
a2.legend(loc="lower left", frameon=False, fontsize=9)

for ax in (a1, a2):
    ax.axvline(cut, color=GREY, ls="--", lw=1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#eeeeee")
a1.text(cut, max(raw) * 1.08, "  Distributor B takes over", color="#555", fontsize=9)
a2.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
plt.tight_layout()
os.makedirs(os.path.join(ROOT, "images"), exist_ok=True)
plt.savefig(os.path.join(ROOT, "images", "raw_vs_clean.png"), dpi=160)
print("saved images/raw_vs_clean.png")
