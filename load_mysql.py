

import os, csv, sys, time, getpass
import pymysql

HOST = os.environ.get("MYSQL_HOST", "localhost")
PORT = int(os.environ.get("MYSQL_PORT", "3306"))
USER = os.environ.get("MYSQL_USER", "root")
PASSWORD = os.environ.get("MYSQL_PASSWORD") or getpass.getpass(f"MySQL password for {USER}@{HOST}: ")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BATCH = 10000

# (table, csv file, column order, converters)
TABLES = [
    ("companies",    "companies.csv",    ["company_id","company_name","country","sector","size","founded_year"],
        {"company_id": int, "founded_year": int}),
    ("skills",       "skills.csv",       ["skill_id","skill_name","category"],
        {"skill_id": int}),
    ("job_postings", "job_postings.csv", ["job_id","company_id","title","country","sector","exp_level",
                                          "remote_type","posted_date","year","salary_min","salary_max"],
        {"job_id": int, "company_id": int, "year": int, "salary_min": int, "salary_max": int}),
    ("skill_demand", "skill_demand.csv", ["demand_id","job_id","skill_id","skill_name","year","country","sector"],
        {"demand_id": int, "job_id": int, "skill_id": int, "year": int}),
    ("salary_data",  "salary_data.csv",  ["salary_id","job_id","key_skill_id","salary_min","salary_max",
                                          "premium_pct","year","country"],
        {"salary_id": int, "job_id": int, "key_skill_id": int, "salary_min": int, "salary_max": int,
         "premium_pct": float, "year": int}),
]

conn = pymysql.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, charset="utf8mb4", autocommit=False)
cur = conn.cursor()

# 1. schema
print("creating schema from mysql_schema.sql ...")
sql = open(os.path.join(HERE, "mysql_schema.sql"), encoding="utf-8").read()
for stmt in sql.split(";"):
    lines = [ln for ln in stmt.splitlines() if not ln.strip().startswith("--")]
    stmt = "\n".join(lines).strip()
    if stmt:
        cur.execute(stmt)
conn.commit()
cur.execute("USE job_market")

# 2. data
for table, fname, cols, conv in TABLES:
    path = os.path.join(DATA, fname)
    if not os.path.exists(path):
        sys.exit(f"missing {path} - run job_generator.py first")
    placeholders = ",".join(["%s"] * len(cols))
    insert = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    t0 = time.time(); n = 0; batch = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            batch.append(tuple(conv[c](row[c]) if c in conv else row[c] for c in cols))
            if len(batch) >= BATCH:
                cur.executemany(insert, batch); n += len(batch); batch = []
        if batch:
            cur.executemany(insert, batch); n += len(batch)
    conn.commit()
    print(f"  {table:<14} {n:>9,} rows  ({time.time()-t0:.1f}s)")

# 3. sanity check
print("\nrow counts in MySQL:")
for table, *_ in TABLES:
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"  {table:<14} {cur.fetchone()[0]:>9,}")
conn.close()
print("\ndone. Database: job_market")
