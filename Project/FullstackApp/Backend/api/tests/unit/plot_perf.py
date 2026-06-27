"""
Citește api/tests/perf_report.txt și generează un chart matplotlib
cu rezultatele testelor de performanță.

Rulare:
    cd FullstackApp/Backend
    venv\\Scripts\\python api/tests/plot_perf.py
"""

import re
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

REPORT_PATH = os.path.join(os.path.dirname(__file__), "perf_report.txt")

# ── parsare ───────────────────────────────────────────────────────────────────

pattern = re.compile(
    r'\[PERF\]\s+(.+?)\s+avg=\s*([\d.]+)ms\s+min=\s*([\d.]+)ms\s+max=\s*([\d.]+)ms\s+sd=\s*([\d.]+)ms'
)

entries = []
with open(REPORT_PATH, encoding="utf-16") as f:
    for line in f:
        m = pattern.search(line)
        if m:
            entries.append({
                "label": m.group(1).strip(),
                "avg":   float(m.group(2)),
                "min":   float(m.group(3)),
                "max":   float(m.group(4)),
                "sd":    float(m.group(5)),
            })

if not entries:
    print("Nu s-au găsit date în", REPORT_PATH)
    exit(1)

# ── separare bcrypt vs rest ───────────────────────────────────────────────────

bcrypt  = [e for e in entries if e["avg"] > 100]
regular = [e for e in entries if e["avg"] <= 100]

# sortare descrescătoare după avg
bcrypt.sort(key=lambda e: e["avg"], reverse=True)
regular.sort(key=lambda e: e["avg"], reverse=True)

THRESHOLD_BCRYPT  = 2000
THRESHOLD_REGULAR = 400

COLOR_OK    = "#22c55e"
COLOR_WARN  = "#f59e0b"
COLOR_ERR   = "#ef4444"
COLOR_ERR_BAR = "#fca5a5"


def bar_color(avg, threshold):
    pct = avg / threshold
    if pct < 0.5:
        return COLOR_OK
    if pct < 0.85:
        return COLOR_WARN
    return COLOR_ERR


# ── figură ────────────────────────────────────────────────────────────────────

fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(16, 7),
    gridspec_kw={"width_ratios": [1, 2.5]},
)
fig.patch.set_facecolor("#0f172a")
fig.suptitle(
    "PageSage AI — Performance Test Results",
    fontsize=15, fontweight="bold", color="white", y=1.01,
)

def style_ax(ax):
    ax.set_facecolor("#1e293b")
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")


# ── subplot 1: bcrypt ─────────────────────────────────────────────────────────

labels1 = [e["label"] for e in bcrypt]
avgs1   = [e["avg"]   for e in bcrypt]
errs1   = [e["sd"]    for e in bcrypt]
colors1 = [bar_color(a, THRESHOLD_BCRYPT) for a in avgs1]
y1      = np.arange(len(labels1))

bars1 = ax1.barh(y1, avgs1, xerr=errs1, color=colors1,
                 error_kw=dict(ecolor=COLOR_ERR_BAR, lw=1.5, capsize=3),
                 height=0.55)
ax1.axvline(THRESHOLD_BCRYPT, color="#f97316", lw=1.5, ls="--", alpha=0.8,
            label=f"Threshold {THRESHOLD_BCRYPT}ms")
ax1.set_yticks(y1)
ax1.set_yticklabels(labels1, fontsize=7.5, color="white")
ax1.set_xlabel("Response time (ms)", fontsize=9)
ax1.set_title("Bcrypt Operations\n(login / signup)", fontsize=10, pad=8)
ax1.set_xscale("log")
ax1.set_xlim(100, THRESHOLD_BCRYPT * 1.5)
ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v)}"))
ax1.legend(fontsize=8, facecolor="#1e293b", labelcolor="white", framealpha=0.6)
style_ax(ax1)

for bar, val in zip(bars1, avgs1):
    ax1.text(val + 5, bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}ms", va="center", fontsize=8, color="white")

# ── subplot 2: regular endpoints ──────────────────────────────────────────────

labels2 = [e["label"] for e in regular]
avgs2   = [e["avg"]   for e in regular]
errs2   = [e["sd"]    for e in regular]
colors2 = [bar_color(a, THRESHOLD_REGULAR) for a in avgs2]
y2      = np.arange(len(labels2))

bars2 = ax2.barh(y2, avgs2, xerr=errs2, color=colors2,
                 error_kw=dict(ecolor=COLOR_ERR_BAR, lw=1.5, capsize=3),
                 height=0.55)
ax2.axvline(THRESHOLD_REGULAR, color="#f97316", lw=1.5, ls="--", alpha=0.8,
            label=f"Threshold {THRESHOLD_REGULAR}ms")
ax2.set_yticks(y2)
ax2.set_yticklabels(labels2, fontsize=7.5, color="white")
ax2.set_xlabel("Response time (ms)", fontsize=9)
ax2.set_title("API Endpoints\n(all modules, AI/Manim mocked)", fontsize=10, pad=8)
ax2.set_xscale("log")
ax2.set_xlim(0.1, THRESHOLD_REGULAR * 1.5)
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}" if v < 10 else f"{int(v)}"))
ax2.legend(fontsize=8, facecolor="#1e293b", labelcolor="white", framealpha=0.6)
style_ax(ax2)

for bar, val in zip(bars2, avgs2):
    ax2.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
             f"{val:.1f}ms", va="center", fontsize=8, color="white")

# ── legenda culori ────────────────────────────────────────────────────────────

legend_patches = [
    mpatches.Patch(color=COLOR_OK,   label="< 50% threshold"),
    mpatches.Patch(color=COLOR_WARN, label="50–85% threshold"),
    mpatches.Patch(color=COLOR_ERR,  label="> 85% threshold"),
]
fig.legend(handles=legend_patches, loc="lower center", ncol=3,
           fontsize=9, facecolor="#1e293b", labelcolor="white",
           framealpha=0.6, bbox_to_anchor=(0.5, -0.04))

# ── sumar text ────────────────────────────────────────────────────────────────

total    = len(entries)
all_pass = all(
    e["avg"] < (THRESHOLD_BCRYPT if e["avg"] > 100 else THRESHOLD_REGULAR)
    for e in entries
)
status   = "ALL PASSED ✓" if all_pass else "SOME FAILED ✗"
fastest  = min(entries, key=lambda e: e["avg"])
slowest  = max(entries, key=lambda e: e["avg"])

summary = (
    f"Tests: {total}/78   |   {status}   |   "
    f"Fastest: {fastest['avg']:.1f}ms ({fastest['label'].split('/')[-1]})   |   "
    f"Slowest: {slowest['avg']:.1f}ms ({slowest['label'].split('(')[0].strip()})"
)
fig.text(0.5, -0.01, summary, ha="center", fontsize=8.5,
         color="#94a3b8", style="italic")

plt.tight_layout()
plt.subplots_adjust(bottom=0.1)

out_path = os.path.join(os.path.dirname(__file__), "perf_chart.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight", pad_inches=0.3, facecolor=fig.get_facecolor())
print(f"Chart salvat: {out_path}")
plt.show()
