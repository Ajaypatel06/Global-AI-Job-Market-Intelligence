# job_generator.py - makes the data for the project (50,000 made-up postings)
# order: job_generator.py, load_mysql.py, analysis.py

import random, csv, os, sqlite3, math
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = "./data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# constants
COUNTRIES = ["India","USA","UK","UAE","Singapore","Canada","Australia","Germany","Netherlands","France"]
SECTORS   = ["Technology","Finance","Healthcare","Retail","Logistics","Manufacturing","Media"]
SIZES     = ["Startup","Mid-size","Enterprise"]
SIZE_W    = [0.30, 0.40, 0.30]

EXP_LEVELS = ["Junior","Mid","Senior","Lead"]
EXP_W      = [0.25, 0.35, 0.28, 0.12]

REMOTE     = ["Remote","Hybrid","Onsite"]
REMOTE_W_BY_YEAR = {
    2021: [0.15, 0.25, 0.60],
    2022: [0.20, 0.32, 0.48],
    2023: [0.22, 0.38, 0.40],
    2024: [0.20, 0.42, 0.38],
    2025: [0.18, 0.45, 0.37],
}

JOB_TITLES = [
    "Data Analyst","Senior Data Analyst","Business Analyst","Product Analyst",
    "Growth Analyst","Analytics Engineer","Data Engineer","ML Engineer",
    "AI/ML Analyst","BI Developer","MIS Analyst","Data Scientist",
    "Research Analyst","Decision Scientist","Marketing Analyst",
]

# 25 skills
SKILLS = [
    # id, name, category
    (1,  "Python",            "Programming"),
    (2,  "SQL",               "Programming"),
    (3,  "Excel",             "Spreadsheet"),
    (4,  "Power BI",          "Visualization"),
    (5,  "Tableau",           "Visualization"),
    (6,  "R",                 "Programming"),
    (7,  "VBA/Macros",        "Spreadsheet"),
    (8,  "LLM APIs",          "AI/ML"),
    (9,  "Machine Learning",  "AI/ML"),
    (10, "Deep Learning",     "AI/ML"),
    (11, "NLP",               "AI/ML"),
    (12, "scikit-learn",      "AI/ML"),
    (13, "TensorFlow/PyTorch","AI/ML"),
    (14, "Cloud (AWS/GCP/Azure)","Cloud"),
    (15, "dbt",               "Data Engineering"),
    (16, "Spark",             "Data Engineering"),
    (17, "Airflow",           "Data Engineering"),
    (18, "Git",               "DevOps"),
    (19, "Docker",            "DevOps"),
    (20, "Pandas/NumPy",      "Programming"),
    (21, "Looker",            "Visualization"),
    (22, "Alteryx",           "Analytics"),
    (23, "SAS",               "Analytics"),
    (24, "MATLAB",            "Analytics"),
    (25, "Power Automate",    "Automation"),
]

# share of postings asking for each skill, per year (the made-up trend lives here)
SKILL_DEMAND = {
    1:  {2021:0.45, 2022:0.58, 2023:0.70, 2024:0.82, 2025:0.88},  # Python
    2:  {2021:0.85, 2022:0.85, 2023:0.86, 2024:0.87, 2025:0.87},  # SQL
    3:  {2021:0.91, 2022:0.88, 2023:0.83, 2024:0.75, 2025:0.67},  # Excel
    4:  {2021:0.35, 2022:0.42, 2023:0.50, 2024:0.55, 2025:0.58},  # Power BI
    5:  {2021:0.42, 2022:0.43, 2023:0.41, 2024:0.39, 2025:0.38},  # Tableau
    6:  {2021:0.28, 2022:0.25, 2023:0.22, 2024:0.20, 2025:0.18},  # R
    7:  {2021:0.30, 2022:0.22, 2023:0.15, 2024:0.10, 2025:0.07},  # VBA
    8:  {2021:0.01, 2022:0.04, 2023:0.18, 2024:0.38, 2025:0.55},  # LLM APIs
    9:  {2021:0.32, 2022:0.38, 2023:0.44, 2024:0.50, 2025:0.55},  # ML
    10: {2021:0.18, 2022:0.22, 2023:0.27, 2024:0.32, 2025:0.35},  # DL
    11: {2021:0.15, 2022:0.20, 2023:0.28, 2024:0.35, 2025:0.40},  # NLP
    12: {2021:0.22, 2022:0.28, 2023:0.35, 2024:0.42, 2025:0.45},  # sklearn
    13: {2021:0.18, 2022:0.22, 2023:0.27, 2024:0.31, 2025:0.34},  # TF/PT
    14: {2021:0.25, 2022:0.32, 2023:0.40, 2024:0.47, 2025:0.52},  # Cloud
    15: {2021:0.02, 2022:0.06, 2023:0.14, 2024:0.22, 2025:0.28},  # dbt
    16: {2021:0.15, 2022:0.20, 2023:0.25, 2024:0.29, 2025:0.32},  # Spark
    17: {2021:0.08, 2022:0.12, 2023:0.18, 2024:0.22, 2025:0.25},  # Airflow
    18: {2021:0.40, 2022:0.48, 2023:0.55, 2024:0.60, 2025:0.63},  # Git
    19: {2021:0.12, 2022:0.18, 2023:0.25, 2024:0.30, 2025:0.34},  # Docker
    20: {2021:0.35, 2022:0.45, 2023:0.55, 2024:0.62, 2025:0.68},  # Pandas
    21: {2021:0.08, 2022:0.12, 2023:0.16, 2024:0.19, 2025:0.22},  # Looker
    22: {2021:0.18, 2022:0.17, 2023:0.16, 2024:0.14, 2025:0.13},  # Alteryx
    23: {2021:0.22, 2022:0.19, 2023:0.16, 2024:0.13, 2025:0.11},  # SAS
    24: {2021:0.12, 2022:0.10, 2023:0.08, 2024:0.07, 2025:0.06},  # MATLAB
    25: {2021:0.10, 2022:0.14, 2023:0.18, 2024:0.22, 2025:0.26},  # Power Automate
}

# country multiplier for AI skills (my assumption, not measured)
COUNTRY_MODIFIER = {
    "USA": 1.15, "Singapore": 1.12, "UK": 1.08, "Canada": 1.06,
    "Australia": 1.04, "Germany": 1.02, "Netherlands": 1.02,
    "UAE": 0.98, "India": 0.95, "France": 0.96,
}

# base salary in USD by country and level
BASE_SALARY = {
    "USA":         {"Junior":65000, "Mid":95000,  "Senior":135000, "Lead":175000},
    "UK":          {"Junior":45000, "Mid":68000,  "Senior":95000,  "Lead":125000},
    "Singapore":   {"Junior":42000, "Mid":65000,  "Senior":92000,  "Lead":120000},
    "Canada":      {"Junior":48000, "Mid":72000,  "Senior":100000, "Lead":130000},
    "Australia":   {"Junior":52000, "Mid":78000,  "Senior":108000, "Lead":140000},
    "Germany":     {"Junior":40000, "Mid":60000,  "Senior":85000,  "Lead":110000},
    "Netherlands": {"Junior":42000, "Mid":62000,  "Senior":88000,  "Lead":115000},
    "France":      {"Junior":36000, "Mid":54000,  "Senior":76000,  "Lead":100000},
    "UAE":         {"Junior":38000, "Mid":58000,  "Senior":82000,  "Lead":108000},
    "India":       {"Junior":8000,  "Mid":14000,  "Senior":22000,  "Lead":32000},
}

# salary premium per AI skill (assumed)
SKILL_PREMIUM = {8:0.22, 9:0.18, 10:0.20, 11:0.17, 13:0.19, 15:0.15, 16:0.14, 17:0.13}

def rand_date(year):
    start = datetime(year, 1, 1)
    end   = datetime(year, 12, 31)
    return start + timedelta(days=random.randint(0, (end-start).days))

def weighted_choice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]

# build companies
print("generating companies...")

COMPANY_NAMES = [
    "Nexus","Apex","Vertex","Orbit","Quantum","Synapse","Atlas","Nova","Zenith","Axon",
    "Prism","Flux","Helix","Cipher","Vortex","Pulse","Nimbus","Stratos","Kova","Lyra",
    "Forge","Slate","Drift","Crest","Lumio","Brio","Chord","Fable","Glint","Halcyon",
    "Inkwell","Jasper","Kindred","Lumen","Mosaic","Nuvelo","Onyx","Paragon","Qubit","Riven",
    "Solace","Tidal","Umbra","Velox","Wren","Xero","Yield","Zephyr","Aero","Basalt",
]

companies = []
cid = 1
for country in COUNTRIES:
    n = 50  # 50 companies per country = 500 total
    for i in range(n):
        base = COMPANY_NAMES[i % len(COMPANY_NAMES)]
        suffix = random.choice(["Technologies","Analytics","Intelligence","Systems","Labs",
                                "Solutions","Ventures","Digital","Data","AI"])
        companies.append({
            "company_id":   cid,
            "company_name": f"{base} {suffix}",
            "country":      country,
            "sector":       random.choice(SECTORS),
            "size":         weighted_choice(SIZES, SIZE_W),
            "founded_year": random.randint(2000, 2022),
        })
        cid += 1

# build job postings, skill demand, salary data
print("generating job postings...")

job_postings  = []
skill_demand  = []
salary_data   = []
jid  = 1
sdid = 1
said = 1

YEARS        = [2021, 2022, 2023, 2024, 2025]
POSTS_PER_YEAR = 10000  # 50,000 total

for year in YEARS:
    for _ in range(POSTS_PER_YEAR):
        company   = random.choice(companies)
        country   = company["country"]
        sector    = company["sector"]
        exp_level = weighted_choice(EXP_LEVELS, EXP_W)
        remote    = weighted_choice(REMOTE, REMOTE_W_BY_YEAR[year])
        title     = random.choice(JOB_TITLES)
        post_date = rand_date(year)

        # Salary
        base  = BASE_SALARY[country][exp_level]
        noise = random.uniform(0.85, 1.15)
        sal_min = int(base * noise * 0.85)
        sal_max = int(base * noise * 1.15)

        job_postings.append({
            "job_id":       jid,
            "company_id":   company["company_id"],
            "title":        title,
            "country":      country,
            "sector":       sector,
            "exp_level":    exp_level,
            "remote_type":  remote,
            "posted_date":  post_date.strftime("%Y-%m-%d"),
            "year":         year,
            "salary_min":   sal_min,
            "salary_max":   sal_max,
        })

        # Skill demand for this posting
        country_mod = COUNTRY_MODIFIER[country]
        has_ai_skill = False
        ai_skill_ids = []

        for skill_id, skill_name, category in SKILLS:
            base_rate = SKILL_DEMAND[skill_id][year]
            # multiplier only applies to AI/ML and data engineering skills
            if category in ("AI/ML","Data Engineering"):
                rate = min(0.95, base_rate * country_mod)
            else:
                rate = base_rate
            # senior roles list a few more skills
            if exp_level in ("Senior","Lead"):
                rate = min(0.95, rate * 1.08)

            if random.random() < rate:
                skill_demand.append({
                    "demand_id":   sdid,
                    "job_id":      jid,
                    "skill_id":    skill_id,
                    "skill_name":  skill_name,
                    "year":        year,
                    "country":     country,
                    "sector":      sector,
                })
                sdid += 1
                if skill_id in SKILL_PREMIUM:
                    has_ai_skill = True
                    ai_skill_ids.append(skill_id)

        # Salary premium record
        if ai_skill_ids:
            top_skill = max(ai_skill_ids, key=lambda x: SKILL_PREMIUM.get(x,0))
            premium   = SKILL_PREMIUM[top_skill]
            salary_data.append({
                "salary_id":     said,
                "job_id":        jid,
                "key_skill_id":  top_skill,
                "salary_min":    sal_min,
                "salary_max":    sal_max,
                "premium_pct":   round(premium * 100, 1),
                "year":          year,
                "country":       country,
            })
            said += 1

        jid += 1

# write csvs
print("writing csvs...")

def write_csv(filename, rows, exclude=None):
    if not rows: return
    keys = [k for k in rows[0].keys() if not (exclude and k in exclude)]
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: row[k] for k in keys})
    print(f"  {filename}: {len(rows):,} rows")

write_csv("companies.csv",    companies)
write_csv("job_postings.csv", job_postings)
write_csv("skill_demand.csv", skill_demand)
write_csv("salary_data.csv",  salary_data)

# Skills reference
skills_rows = [{"skill_id":s[0],"skill_name":s[1],"category":s[2]} for s in SKILLS]
write_csv("skills.csv", skills_rows)

# sqlite copy is off by default (the project uses MySQL). BUILD_SQLITE=1 turns it on
if os.environ.get("BUILD_SQLITE") == "1":
    # build sqlite db
    print("building db...")

    db  = sqlite3.connect(f"{OUTPUT_DIR}/job_market.db")
    cur = db.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS companies;
    DROP TABLE IF EXISTS job_postings;
    DROP TABLE IF EXISTS skills;
    DROP TABLE IF EXISTS skill_demand;
    DROP TABLE IF EXISTS salary_data;

    CREATE TABLE companies (
        company_id INT PRIMARY KEY, company_name TEXT, country TEXT,
        sector TEXT, size TEXT, founded_year INT
    );
    CREATE TABLE job_postings (
        job_id INT PRIMARY KEY, company_id INT, title TEXT, country TEXT,
        sector TEXT, exp_level TEXT, remote_type TEXT, posted_date TEXT,
        year INT, salary_min INT, salary_max INT
    );
    CREATE TABLE skills (
        skill_id INT PRIMARY KEY, skill_name TEXT, category TEXT
    );
    CREATE TABLE skill_demand (
        demand_id INT PRIMARY KEY, job_id INT, skill_id INT,
        skill_name TEXT, year INT, country TEXT, sector TEXT
    );
    CREATE TABLE salary_data (
        salary_id INT PRIMARY KEY, job_id INT, key_skill_id INT,
        salary_min INT, salary_max INT, premium_pct REAL, year INT, country TEXT
    );
    CREATE INDEX idx_sd_skill ON skill_demand(skill_id);
    CREATE INDEX idx_sd_year  ON skill_demand(year);
    CREATE INDEX idx_jp_year  ON job_postings(year);
    CREATE INDEX idx_jp_country ON job_postings(country);
    CREATE INDEX idx_sd_job   ON skill_demand(job_id);
    CREATE INDEX idx_sal_job  ON salary_data(job_id);
    """)

    cur.executemany("INSERT INTO companies VALUES (?,?,?,?,?,?)",
        [(c["company_id"],c["company_name"],c["country"],c["sector"],c["size"],c["founded_year"])
         for c in companies])
    cur.executemany("INSERT INTO job_postings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [(j["job_id"],j["company_id"],j["title"],j["country"],j["sector"],
          j["exp_level"],j["remote_type"],j["posted_date"],j["year"],
          j["salary_min"],j["salary_max"]) for j in job_postings])
    cur.executemany("INSERT INTO skills VALUES (?,?,?)",
        [(s[0],s[1],s[2]) for s in SKILLS])
    cur.executemany("INSERT INTO skill_demand VALUES (?,?,?,?,?,?,?)",
        [(s["demand_id"],s["job_id"],s["skill_id"],s["skill_name"],
          s["year"],s["country"],s["sector"]) for s in skill_demand])
    cur.executemany("INSERT INTO salary_data VALUES (?,?,?,?,?,?,?,?)",
        [(s["salary_id"],s["job_id"],s["key_skill_id"],s["salary_min"],
          s["salary_max"],s["premium_pct"],s["year"],s["country"]) for s in salary_data])
    db.commit()

    # summary
    print("\ndataset summary:")
    for tbl in ["companies","job_postings","skills","skill_demand","salary_data"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl:<20} {n:>10,} rows")

    # quick check of a few skills
    print("\nskill demand check:")
    totals = dict(cur.execute("SELECT year, COUNT(*) FROM job_postings GROUP BY year").fetchall())
    for sid, sname in [(1,"Python"),(8,"LLM APIs"),(3,"Excel"),(7,"VBA/Macros"),(2,"SQL")]:
        rows = cur.execute(
            "SELECT year, COUNT(DISTINCT job_id) FROM skill_demand WHERE skill_id=? GROUP BY year",
            (sid,)).fetchall()
        vals = {y: round(n * 100.0 / totals[y], 1) for y, n in rows}
        print(f"  {sname:<20} 2021:{vals.get(2021,'?')}%  ->  2025:{vals.get(2025,'?')}%")

    db.close()
    print(f"\n  DB: {OUTPUT_DIR}/job_market.db")

print("\nCSV files written to ./data  ->  next: python load_mysql.py")
print("\ndone.")
