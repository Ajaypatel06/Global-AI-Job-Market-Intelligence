# analysis.py - runs the SQL on MySQL and saves 6 charts to charts/
# run after load_mysql.py

import getpass
from decimal import Decimal
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import warnings, os

warnings.filterwarnings("ignore")

# MySQL login: set MYSQL_PASSWORD (MYSQL_USER, MYSQL_HOST, MYSQL_PORT are optional)
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD") or getpass.getpass(f"MySQL password for {MYSQL_USER}@{MYSQL_HOST}: ")
OUT_DIR = "./charts"
os.makedirs(OUT_DIR, exist_ok=True) 

DARK   = "#0D0D1A"
MID    = "#16213E"
BORDER = "#252540"
ACCENT = "#FF6B35"
CYAN   = "#4ECDC4"
WHITE  = "#F5F5F0"
GREY   = "#7A7A9A"
PALETTE= ["#FF6B35","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7",
          "#DDA0DD","#98FB98","#F0E68C","#87CEEB","#FFA07A"]

plt.rcParams.update({
    "figure.facecolor": DARK, "axes.facecolor": MID,
    "axes.edgecolor": BORDER, "axes.labelcolor": WHITE,
    "xtick.color": GREY, "ytick.color": GREY, "text.color": WHITE,
    "grid.color": BORDER, "grid.linewidth": 0.6,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False, "axes.spines.right": False,
})

# small 'simulated data' note on every chart
_orig_savefig = plt.savefig
def _savefig(path, *a, **k):
    plt.gcf().text(0.995, 0.004, "Simulated dataset  |  Ajay Patel", ha="right",
                   va="bottom", fontsize=7.5, color=GREY)
    _orig_savefig(path, *a, **k)
plt.savefig = _savefig

engine = create_engine(URL.create("mysql+pymysql", username=MYSQL_USER, password=MYSQL_PASSWORD,
                                  host=MYSQL_HOST, port=MYSQL_PORT, database="job_market"))

def q(sql, params=None):
    """Run a query on MySQL; DECIMAL columns come back as Decimal, so convert them to float for plotting."""
    with engine.connect() as c:
        df = pd.read_sql_query(text(sql), c, params=params)
    for col in df.columns:
        if df[col].dtype == object and df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df

print("running analysis...")

# load demand trend data
trend_sql = """
WITH yt AS (SELECT year, COUNT(DISTINCT job_id) total FROM job_postings GROUP BY year),
sy AS (SELECT skill_name, year, COUNT(DISTINCT job_id) cnt FROM skill_demand GROUP BY skill_name, year)
SELECT sy.skill_name, sy.year, ROUND(sy.cnt*100.0/yt.total,1) demand_pct
FROM sy JOIN yt ON sy.year=yt.year ORDER BY sy.skill_name, sy.year
"""
trend_df = q(trend_sql)

# skill demand trends
print("  skill demand trends...")

focus_skills = ["Python","SQL","Excel","LLM APIs","Power BI",
                "Machine Learning","Cloud (AWS/GCP/Azure)","VBA/Macros","dbt","Pandas/NumPy"]

fig, ax = plt.subplots(figsize=(13, 7.6))
fig.patch.set_facecolor(DARK)
ends = []

for idx, skill in enumerate(focus_skills):
    sdf = trend_df[trend_df.skill_name == skill]
    style = "-" if skill not in ("VBA/Macros","Excel","SAS") else "--"
    lw    = 2.8 if skill in ("Python","LLM APIs","SQL") else 1.8
    color = ACCENT if skill == "Python" else CYAN if skill == "LLM APIs" else PALETTE[idx % len(PALETTE)]
    ax.plot(sdf.year, sdf.demand_pct, marker="o", markersize=4,
            lw=lw, linestyle=style, color=color, label=skill, alpha=0.90)
    # spread the end labels out so they don't overlap
    last = sdf[sdf.year == 2025]
    if not last.empty:
        ends.append([float(last.demand_pct.values[0]), skill, color])

ends.sort(key=lambda e: e[0])
for i in range(1, len(ends)):
    if ends[i][0] - ends[i-1][0] < 3.4:
        ends[i][0] = ends[i-1][0] + 3.4
for y, skill, color in ends:
    real = float(trend_df[(trend_df.skill_name == skill) & (trend_df.year == 2025)].demand_pct.values[0])
    ax.text(2025.1, y, f"{skill} {real:.0f}%", fontsize=8.5, color=color, va="center")

ax.set_xlim(2020.8, 2026.5)
ax.set_xticks([2021,2022,2023,2024,2025])
ax.set_ylabel("% of Job Postings Requiring Skill", fontsize=11)
ax.set_title("Global AI Skill Demand Trends - 2021 to 2025\n50,000 Job Postings · 10 Countries",
             fontsize=13, fontweight="bold", color=WHITE, pad=14)
ax.grid(alpha=0.3)
ax.legend(facecolor=MID, edgecolor=BORDER, labelcolor=WHITE, fontsize=8.5,
          loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=5)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/01_skill_demand_trends.png", dpi=150, bbox_inches="tight")
plt.close()

# fastest growing vs declining
print("  growth vs decline...")

growth_sql = """
WITH d AS (
    SELECT sd.skill_name, sk.category,
        ROUND(SUM(CASE WHEN sd.year=2021 THEN 1.0 ELSE 0 END)
              /(SELECT COUNT(*) FROM job_postings WHERE year=2021)*100,1) d2021,
        ROUND(SUM(CASE WHEN sd.year=2025 THEN 1.0 ELSE 0 END)
              /(SELECT COUNT(*) FROM job_postings WHERE year=2025)*100,1) d2025
    FROM skill_demand sd JOIN skills sk ON sd.skill_id=sk.skill_id
    GROUP BY sd.skill_name, sk.category
)
SELECT skill_name, category, d2021, d2025, ROUND(d2025-d2021,1) change_pp
FROM d ORDER BY change_pp DESC
"""
gdf = q(growth_sql)
top_grow = gdf.head(8)
top_decl = gdf[gdf.change_pp < 0].tail(6)
plot_df  = pd.concat([top_grow, top_decl]).sort_values("change_pp")

colors = [ACCENT if v > 0 else "#FF4757" for v in plot_df.change_pp]
fig, ax = plt.subplots(figsize=(11, 7))
fig.patch.set_facecolor(DARK)
bars = ax.barh(plot_df.skill_name, plot_df.change_pp, color=colors, alpha=0.88, height=0.6)
for bar, val, d21, d25 in zip(bars, plot_df.change_pp,
                               plot_df.d2021, plot_df.d2025):
    x = val + 0.3 if val >= 0 else 0.6
    ha = "left"
    ax.text(x, bar.get_y()+bar.get_height()/2,
            f"{d21:.0f}% -> {d25:.0f}%", va="center", fontsize=9, color=WHITE, ha=ha)
ax.axvline(0, color=GREY, lw=1, alpha=0.5)
ax.set_xlabel("Change in Demand (percentage points, 2021->2025)", fontsize=11)
ax.set_title("Fastest Growing & Fastest Declining Skills\nGlobal Job Market 2021–2025",
             fontsize=13, fontweight="bold", color=WHITE, pad=14)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/02_fastest_growing.png", dpi=150, bbox_inches="tight")
plt.close()

# country heatmap (2025)
print("  country heatmap...")

country_sql = """
WITH ct AS (SELECT country, COUNT(DISTINCT job_id) total FROM job_postings WHERE year=2025 GROUP BY country),
cs AS (SELECT sd.country, sd.skill_name, COUNT(DISTINCT sd.job_id) cnt
       FROM skill_demand sd WHERE sd.year=2025 GROUP BY sd.country, sd.skill_name)
SELECT cs.country, cs.skill_name, ROUND(cs.cnt*100.0/ct.total,1) pct
FROM cs JOIN ct ON cs.country=ct.country
WHERE cs.skill_name IN ('Python','SQL','LLM APIs','Machine Learning',
                         'Cloud (AWS/GCP/Azure)','Power BI','dbt','Excel')
"""
cdf = q(country_sql)
heat = cdf.pivot(index="country", columns="skill_name", values="pct").fillna(0)

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor(DARK)
sns.heatmap(heat, ax=ax, annot=True, fmt=".0f", cmap="YlOrRd",
            linewidths=0.4, linecolor=DARK,
            cbar_kws={"label":"% of 2025 Job Postings","shrink":0.8},
            annot_kws={"size":9,"color":"black","weight":"bold"})
ax.set_title("AI Skill Demand by Country - 2025\n(% of job postings requiring each skill)",
             fontsize=13, fontweight="bold", color=WHITE, pad=14)
ax.set_xlabel("Skill", fontsize=11)
ax.set_ylabel("Country", fontsize=11)
ax.tick_params(colors=WHITE, rotation=25)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/03_country_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()

# skill half-life index
print("  skill half-life...")

hl_sql = """
WITH d AS (
    SELECT sd.skill_name,
        ROUND(SUM(CASE WHEN sd.year=2021 THEN 1.0 ELSE 0 END)
              /(SELECT COUNT(*) FROM job_postings WHERE year=2021)*100,2) d2021,
        ROUND(SUM(CASE WHEN sd.year=2025 THEN 1.0 ELSE 0 END)
              /(SELECT COUNT(*) FROM job_postings WHERE year=2025)*100,2) d2025
    FROM skill_demand sd GROUP BY sd.skill_name
),
declining AS (
    SELECT skill_name, d2021, d2025,
           (d2025-d2021)/4.0 annual_change
    FROM d WHERE d2025 < d2021 AND d2021 > 0
)
SELECT skill_name, d2021, d2025, annual_change,
       ROUND(-d2021/(2*annual_change),1) half_life_years
FROM declining WHERE annual_change < 0
ORDER BY half_life_years ASC LIMIT 10
"""
hldf = q(hl_sql)

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(DARK)
colors_hl = [ACCENT if v < 5 else "#FFA07A" if v < 10 else CYAN for v in hldf.half_life_years]
bars = ax.barh(hldf.skill_name, hldf.half_life_years, color=colors_hl, alpha=0.88, height=0.6)
for bar, hl, d21, d25 in zip(bars, hldf.half_life_years, hldf.d2021, hldf.d2025):
    ax.text(hl + 0.2, bar.get_y()+bar.get_height()/2,
            f"{hl}y  ({d21:.0f}%->{d25:.0f}%)", va="center", fontsize=9.5, color=WHITE)
ax.axvline(5,  color=ACCENT, lw=1.2, linestyle="--", alpha=0.5)
ax.axvline(10, color=CYAN,   lw=1.2, linestyle="--", alpha=0.5)
ax.text(5.1,  -0.7, "Near-Obsolete", fontsize=8, color=ACCENT)
ax.text(10.1, -0.7, "Fading",        fontsize=8, color=CYAN)
ax.set_xlabel("Estimated Years Until Demand Halves", fontsize=11)
ax.set_title("Skill Half-Life Index - How Long Before These Skills Become Obsolete?",
             fontsize=12, fontweight="bold", color=WHITE, pad=14)
ax.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/04_skill_halflife.png", dpi=150, bbox_inches="tight")
plt.close()

# salary premium by skill
print("  salary premium...")

sal_sql = """
SELECT sk.skill_name, ROUND(AVG(sd.premium_pct),1) avg_premium,
       COUNT(*) n_postings
FROM salary_data sd JOIN skills sk ON sd.key_skill_id=sk.skill_id
GROUP BY sk.skill_name ORDER BY avg_premium DESC
"""
sdf = q(sal_sql)

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(DARK)
colors_s = [ACCENT if v >= 18 else CYAN if v >= 14 else GREY for v in sdf.avg_premium]
bars = ax.bar(sdf.skill_name, sdf.avg_premium, color=colors_s, alpha=0.88, width=0.6)
for bar, val in zip(bars, sdf.avg_premium):
    ax.text(bar.get_x()+bar.get_width()/2, val+0.2, f"+{val}%",
            ha="center", fontsize=10, fontweight="bold", color=WHITE)
ax.axhline(sdf.avg_premium.mean(), color=WHITE, lw=1.2, linestyle="--", alpha=0.5)
ax.text(len(sdf)-0.5, sdf.avg_premium.mean()+0.3,
        f"Avg {sdf.avg_premium.mean():.1f}%", fontsize=8.5, color=GREY)
ax.set_ylabel("Average Salary Premium (%)", fontsize=11)
ax.set_title("AI/ML Skill Salary Premium - Global 2021–2025\n(vs baseline analyst salary for same role)",
             fontsize=12, fontweight="bold", color=WHITE, pad=14)
ax.set_xticklabels(sdf.skill_name, rotation=20, ha="right", fontsize=9.5)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/05_salary_premium.png", dpi=150, bbox_inches="tight")
plt.close()

# remote work trend
print("  remote work trend...")

remote_sql = """
SELECT year,
    ROUND(SUM(CASE WHEN remote_type='Remote' THEN 100.0 ELSE 0 END)/COUNT(*),1) remote_pct,
    ROUND(SUM(CASE WHEN remote_type='Hybrid' THEN 100.0 ELSE 0 END)/COUNT(*),1) hybrid_pct,
    ROUND(SUM(CASE WHEN remote_type='Onsite' THEN 100.0 ELSE 0 END)/COUNT(*),1) onsite_pct
FROM job_postings GROUP BY year ORDER BY year
"""
rdf = q(remote_sql)

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(DARK)
x = rdf.year.astype(int)
ax.stackplot(x, rdf.remote_pct, rdf.hybrid_pct, rdf.onsite_pct,
             labels=["Remote","Hybrid","Onsite"],
             colors=[ACCENT, CYAN, GREY], alpha=0.82)
ax.set_xticks(x)
ax.set_ylabel("% of Job Postings", fontsize=11)
ax.set_title("Remote Work Trend in Analytics/AI Roles - Global 2021–2025",
             fontsize=13, fontweight="bold", color=WHITE, pad=14)
ax.legend(facecolor=MID, edgecolor=BORDER, labelcolor=WHITE, fontsize=10,
          loc="upper right")
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT_DIR}/06_remote_trend.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"\ncharts saved to {OUT_DIR}")
engine.dispose()
