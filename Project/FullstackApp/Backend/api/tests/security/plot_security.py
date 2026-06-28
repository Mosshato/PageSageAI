"""
Reads the latest security_summary_*.json from reports/ and generates
a PNG with two charts:
  - left : summary per security property (SEC-1 ... SEC-5)
  - right: individual result for each test (23 bars)

Usage:
    cd FullstackApp/Backend
    venv\\Scripts\\python api/tests/security/plot_security.py
"""

import json
import os
import glob
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── find the latest JSON ─────────────────────────────────────────────────────

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
jsons = sorted(glob.glob(os.path.join(REPORTS_DIR, "security_summary_*.json")))
if not jsons:
    print("No security_summary_*.json found in", REPORTS_DIR)
    print("Run first: .\\api\\tests\\security\\run_security_tests.ps1")
    exit(1)

latest = jsons[-1]
print(f"Reading: {latest}")

with open(latest, encoding="utf-8-sig") as f:
    data = json.load(f)

results     = data["results"]           # lista de {id, status, detail}
total       = data["total_tests"]
duration    = data["duration"]
global_res  = data["global_result"]
generated   = data["generated_at"]

# ── colors (same as plot_perf.py) ────────────────────────────────────────────

COLOR_OK      = "#22c55e"
COLOR_ERR     = "#ef4444"
COLOR_WARN    = "#f59e0b"
COLOR_ERR_BAR = "#fca5a5"
BG_FIGURE     = "#0f172a"
BG_AXES       = "#1e293b"
BORDER        = "#334155"
TEXT          = "white"
SUBTEXT       = "#94a3b8"

# ── group by property (prefix SEC-N) ─────────────────────────────────────────

PROPERTIES = ["SEC-1", "SEC-2", "SEC-3", "SEC-4", "SEC-5"]
PROP_NAMES = {
    "SEC-1": "Unauthenticated\naccess blocked",
    "SEC-2": "Invalid tokens\nrejected",
    "SEC-3": "Ownership\nisolation",
    "SEC-4": "Role\nseparation",
    "SEC-5": "Passwords stored\nas hash",
}

prop_pass  = {p: 0 for p in PROPERTIES}
prop_fail  = {p: 0 for p in PROPERTIES}
prop_total = {p: 0 for p in PROPERTIES}

for r in results:
    sec_id = r["id"]                         # ex. "SEC-2a"
    prefix = sec_id[:5]                      # ex. "SEC-2"
    if prefix not in prop_pass:
        prefix = sec_id[:4] + "-" + sec_id[4]   # fallback (nu ar trebui)
    if prefix in prop_pass:
        prop_total[prefix] += 1
        if r["status"] == "PASS":
            prop_pass[prefix] += 1
        else:
            prop_fail[prefix] += 1

# ── figura ────────────────────────────────────────────────────────────────────

fig, (ax1, ax2) = plt.subplots(
    1, 2,
    figsize=(20, 9),
    gridspec_kw={"width_ratios": [1, 1.8]},
)
fig.patch.set_facecolor(BG_FIGURE)
fig.suptitle(
    "PageSage AI — Security Test Results",
    fontsize=15, fontweight="bold", color=TEXT, y=1.01,
)


def style_ax(ax):
    ax.set_facecolor(BG_AXES)
    ax.tick_params(colors=TEXT, labelsize=8.5)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)


# ── subplot 1: summary per property ──────────────────────────────────────────

y1     = np.arange(len(PROPERTIES))
pass_v = [prop_pass[p]  for p in PROPERTIES]
fail_v = [prop_fail[p]  for p in PROPERTIES]
tot_v  = [prop_total[p] for p in PROPERTIES]
labels1 = [PROP_NAMES[p] for p in PROPERTIES]

bars_pass = ax1.barh(y1, pass_v, color=COLOR_OK,  height=0.52, label="PASS")
bars_fail = ax1.barh(y1, fail_v, left=pass_v, color=COLOR_ERR, height=0.52, label="FAIL")

ax1.set_yticks(y1)
ax1.set_yticklabels(labels1, fontsize=9, color=TEXT)
ax1.set_xlabel("Number of tests", fontsize=9)
ax1.set_title("Summary by security\nproperty", fontsize=10, pad=10)
ax1.set_xlim(0, max(tot_v) + 1.5)
ax1.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

# bar labels
for bar, p, f, t in zip(bars_pass, pass_v, fail_v, tot_v):
    label = f"{p}/{t} PASS" if f == 0 else f"{p}/{t}"
    ax1.text(
        t + 0.1, bar.get_y() + bar.get_height() / 2,
        label, va="center", fontsize=8.5,
        color=COLOR_OK if f == 0 else COLOR_WARN,
        fontweight="bold",
    )

legend_patches = [
    mpatches.Patch(color=COLOR_OK,  label="PASS"),
    mpatches.Patch(color=COLOR_ERR, label="FAIL"),
]
ax1.legend(handles=legend_patches, fontsize=8.5, facecolor=BG_AXES,
           labelcolor=TEXT, framealpha=0.6, loc="lower right")
style_ax(ax1)

# ── subplot 2: individual tests ───────────────────────────────────────────────

# order: grouped by property, alphabetical by id
def sort_key(r):
    sid = r["id"]           # "SEC-1", "SEC-2a", ...
    num = sid[4]            # cifra
    sub = sid[5:] if len(sid) > 5 else ""
    return (num, sub)

sorted_results = sorted(results, key=sort_key, reverse=True)

labels2 = []
colors2 = []
widths2 = []

for r in sorted_results:
    is_pass = r["status"] == "PASS"
    colors2.append(COLOR_OK if is_pass else COLOR_ERR)
    widths2.append(1.0 if is_pass else 1.0)

    # short label: ID + first ~42 chars of detail
    detail = r["detail"]
    if len(detail) > 44:
        detail = detail[:41] + "..."
    labels2.append(f"[{r['id']}]  {detail}")

y2 = np.arange(len(labels2))

bars2 = ax2.barh(y2, widths2, color=colors2, height=0.60)

# PASS / FAIL marker at end of bar
for bar, r in zip(bars2, sorted_results):
    is_pass = r["status"] == "PASS"
    ax2.text(
        1.02, bar.get_y() + bar.get_height() / 2,
        "PASS" if is_pass else "FAIL",
        va="center", fontsize=8, color=COLOR_OK if is_pass else COLOR_ERR,
        fontweight="bold",
    )

ax2.set_yticks(y2)
ax2.set_yticklabels(labels2, fontsize=7.5, color=TEXT)
ax2.set_xlim(0, 1.18)
ax2.set_xticks([])
ax2.set_title(f"Individual results - {total} tests", fontsize=10, pad=10)

# subtle horizontal lines for readability
for yi in y2:
    ax2.axhline(yi, color=BORDER, lw=0.4, alpha=0.5)

style_ax(ax2)

# ── summary text ─────────────────────────────────────────────────────────────

total_pass = sum(1 for r in results if r["status"] == "PASS")
total_fail = total - total_pass
status_str = "ALL PASSED" if total_fail == 0 else f"{total_fail} FAILED"

summary = (
    f"Tests: {total_pass}/{total} PASSED   |   {status_str}   |   "
    f"Duration: {duration}   |   Generated: {generated}"
)
fig.text(0.5, -0.01, summary, ha="center", fontsize=8.5,
         color=SUBTEXT, style="italic")

# ── save ─────────────────────────────────────────────────────────────────────

plt.tight_layout()
plt.subplots_adjust(bottom=0.08, wspace=0.55)

out_path = os.path.join(REPORTS_DIR, "security_chart.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight",
            pad_inches=0.3, facecolor=fig.get_facecolor())
print(f"Chart saved: {out_path}")
plt.show()
