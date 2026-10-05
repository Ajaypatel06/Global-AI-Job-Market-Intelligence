# facts.py - pulls the headline numbers out of MySQL (reusing the queries in mysql_queries.sql)
# and writes facts.json. run after load_mysql.py

import re, json, os, getpass, warnings
from decimal import Decimal
import pandas as pd
import pymysql

warnings.filterwarnings("ignore")
db = pymysql.connect(host=os.environ.get("MYSQL_HOST", "localhost"), port=int(os.environ.get("MYSQL_PORT", "3306")),
                     user=os.environ.get("MYSQL_USER", "root"),
                     password=os.environ.get("MYSQL_PASSWORD") or getpass.getpass("MySQL password: "),
                     database="job_market")

sql_text = open("mysql_queries.sql", encoding="utf-8").read()
parts = re.split(r"(?m)^-- (Q\d+):", sql_text)
Q = {parts[i]: "-- " + parts[i + 1] for i in range(1, len(parts), 2)}
def run(sql, params=None):
    df = pd.read_sql_query(sql, db, params=params)
    for col in df.columns:
        if df[col].dtype == object and df[col].map(lambda v: isinstance(v, Decimal)).any():
            df[col] = df[col].astype(float)
    return df

def rows(sql):
    cur = db.cursor(); cur.execute(sql); return cur.fetchall()

F = {}
YRS = [2021, 2022, 2023, 2024, 2025]

# Q1: demand % by skill and year
q1 = run(Q["Q1"])
F["pct"] = {s: {str(int(r.year)): float(r.demand_pct) for r in g.itertuples()} for s, g in q1.groupby("skill_name")}

# Q2: change in percentage points + relative growth
q2 = run(Q["Q2"])
F["change"] = {r.skill_name: float(r.absolute_growth_pp) for r in q2.itertuples()}
F["change"] = dict(sorted(F["change"].items(), key=lambda x: -x[1]))
F["rel_growth"] = {r.skill_name: int(r.relative_growth_pct) for r in q2.itertuples()}
F["llm_rel_growth"] = F["rel_growth"]["LLM APIs"]
F["dbt_rel_growth"] = F["rel_growth"]["dbt"]

# Q4: half-life (linear model)
q4 = run(Q["Q4"])
F["halflife"] = {r.skill_name: float(r.half_life_years) for r in q4.itertuples()}

# Q5: salary premium by skill
q5 = run(Q["Q5"])
F["premium"] = {r.skill_name: float(r.avg_premium_pct) for r in q5.itertuples()}
F["premium_avg_of_skills"] = round(sum(F["premium"].values()) / len(F["premium"]), 1)

# Q6: remote / hybrid / onsite
q6 = run(Q["Q6"])
F["remote"] = {str(int(r.year)): {"Remote": float(r.remote_pct), "Hybrid": float(r.hybrid_pct), "Onsite": float(r.onsite_pct)} for r in q6.itertuples()}

# country x skill demand 2025 (same as Q3 but with more skills)
c = run("""
WITH ct AS (SELECT country, COUNT(DISTINCT job_id) total FROM job_postings WHERE year=2025 GROUP BY country),
cs AS (SELECT country, skill_name, COUNT(DISTINCT job_id) n FROM skill_demand WHERE year=2025 GROUP BY country, skill_name)
SELECT cs.country, cs.skill_name, ROUND(cs.n*100.0/ct.total,1) demand_pct FROM cs JOIN ct ON cs.country=ct.country
""")
F["country"] = {k: {r.skill_name: float(r.demand_pct) for r in g.itertuples()} for k, g in c.groupby("country")}

# country x year demand for Python and LLM APIs (trend lines)
cy = run("""
WITH ct AS (SELECT country, year, COUNT(*) total FROM job_postings GROUP BY country, year),
cs AS (SELECT country, year, skill_name, COUNT(DISTINCT job_id) n FROM skill_demand
       WHERE skill_name IN ('Python','LLM APIs') GROUP BY country, year, skill_name)
SELECT cs.country, cs.year, cs.skill_name, ROUND(cs.n*100.0/ct.total,1) demand_pct
FROM cs JOIN ct ON cs.country=ct.country AND cs.year=ct.year
""")
F["country_year"] = {k: {s: {str(int(r.year)): float(r.demand_pct) for r in g2.itertuples()} for s, g2 in g.groupby("skill_name")} for k, g in cy.groupby("country")}

# co-occurrence 2025 (same expression as Q7)
def co(a, b):
    r = run("""SELECT ROUND(COUNT(*)*100.0/(SELECT COUNT(DISTINCT job_id) FROM job_postings WHERE year=2025),1) p
               FROM skill_demand x JOIN skill_demand y ON x.job_id=y.job_id
               WHERE x.year=2025 AND y.year=2025 AND x.skill_name=%s AND y.skill_name=%s""", (a, b))
    return float(r.p[0])
F["co"] = {"Python+SQL": co("Python", "SQL"), "Python+LLM APIs": co("Python", "LLM APIs"),
           "SQL+LLM APIs": co("SQL", "LLM APIs"), "Python+Pandas": co("Python", "Pandas/NumPy")}

# Q10: country x experience salary midpoint, 2025
q10 = run(Q["Q10"])
F["salary_mid"] = {k: {r.exp_level: int(r.avg_mid_salary) for r in g.itertuples()} for k, g in q10.groupby("country")}

# counts and misc
one = lambda sql: int(rows(sql)[0][0])
F["counts"] = {"jobs": one("SELECT COUNT(*) FROM job_postings"), "companies": one("SELECT COUNT(DISTINCT company_id) FROM job_postings"),
               "countries": one("SELECT COUNT(DISTINCT country) FROM job_postings"), "skills": one("SELECT COUNT(*) FROM skills"),
               "skill_demand": one("SELECT COUNT(*) FROM skill_demand"), "salary_rows": one("SELECT COUNT(*) FROM salary_data"),
               "categories": one("SELECT COUNT(DISTINCT category) FROM skills")}
F["sql_range"] = [F["pct"]["SQL"][str(y)] for y in YRS]
F["sector_2025"] = {k: int(v) for k, v in rows("SELECT sector, COUNT(*) n FROM job_postings WHERE year=2025 GROUP BY sector ORDER BY n DESC")}
F["country_postings"] = {k: int(v) for k, v in rows("SELECT country, COUNT(*) n FROM job_postings GROUP BY country ORDER BY n DESC")}
F["category"] = {k: v for k, v in rows("SELECT skill_name, category FROM skills")}
F["powerbi_2025"] = {k: float(v) for k, v in rows("""
    SELECT sd.country, ROUND(COUNT(DISTINCT sd.job_id)*100.0/(SELECT COUNT(*) FROM job_postings jp WHERE jp.year=2025 AND jp.country=sd.country),1)
    FROM skill_demand sd WHERE sd.year=2025 AND sd.skill_name='Power BI' GROUP BY sd.country""")}
F["skills_2025_postings"] = {k: int(v) for k, v in rows("SELECT skill_name, COUNT(DISTINCT job_id) FROM skill_demand WHERE year=2025 GROUP BY skill_name")}

json.dump(F, open("facts.json", "w"), indent=1)
g = lambda s, y: F["pct"][s][str(y)]
print(f"Python {g('Python',2021)}% -> {g('Python',2025)}% | LLM APIs {g('LLM APIs',2021)}% -> {g('LLM APIs',2025)}% (+{F['llm_rel_growth']:,}%)")
print(f"SQL {F['sql_range']} | Excel {g('Excel',2021)}% -> {g('Excel',2025)}% | VBA {g('VBA/Macros',2021)}% -> {g('VBA/Macros',2025)}%")
print("half-life (years):", F["halflife"])
print("USA vs India LLM APIs 2025:", F["country"]["USA"]["LLM APIs"], F["country"]["India"]["LLM APIs"])
print("remote 2025:", F["remote"]["2025"], "| co-occurrence:", F["co"])
