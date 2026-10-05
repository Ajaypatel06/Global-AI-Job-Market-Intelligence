# data_cleaning.py
# job_postings.csv from the generator has no real mess in it, so this script makes a dirty copy first
# (bad country names, mixed date formats, dupes, missing salaries) and then cleans it back up.
# the dirty file is simulated, it is only here to show the cleaning steps.
# run after job_generator.py

import pandas as pd
import numpy as np
import random
import re

random.seed(7)
np.random.seed(7)

SRC  = "./data/job_postings.csv"
RAW  = "./data/job_postings_raw_dirty.csv"   # the deliberately messy version
OUT  = "./data/job_postings_cleaned.csv"     # the cleaned-back-up version
REPORT = "./charts/data_cleaning_report.txt"

# make the dirty copy
print("building simulated messy raw export...")
df = pd.read_csv(SRC)
dirty = df.copy()

COUNTRY_VARIANTS = {
    "USA":   ["USA", "U.S.A", "United States", "usa", " USA"],
    "UK":    ["UK", "U.K.", "United Kingdom", "uk"],
    "India": ["India", "india", "IN", " India"],
}
EXP_TYPOS = {
    "Junior": ["Junior", "junior", "JUNIOR", "Jr"],
    "Mid":    ["Mid", "mid", "Mid-level", " Mid"],
    "Senior": ["Senior", "senior", "Snr", "SENIOR "],
    "Lead":   ["Lead", "lead", "LEAD"],
}
DATE_FORMATS = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]

n = len(dirty)
idx = np.arange(n)

# 1. inconsistent country naming (~8% of rows for countries we have variants for)
for country, variants in COUNTRY_VARIANTS.items():
    mask = dirty["country"] == country
    rows = dirty[mask].sample(frac=0.5, random_state=1).index
    dirty.loc[rows, "country"] = [random.choice(variants) for _ in rows]

# 2. mixed date formats (~40% of rows reformatted away from ISO)
reformat_idx = np.random.choice(idx, size=int(n * 0.40), replace=False)
def reformat_date(d, fmt):
    dt = pd.to_datetime(d)
    return dt.strftime(fmt)
for i in reformat_idx:
    fmt = random.choice(DATE_FORMATS[1:])
    dirty.at[i, "posted_date"] = reformat_date(dirty.at[i, "posted_date"], fmt)

# 3. typo'd / inconsistent experience level casing (~15% of rows)
typo_idx = np.random.choice(idx, size=int(n * 0.15), replace=False)
for i in typo_idx:
    lvl = dirty.at[i, "exp_level"]
    if lvl in EXP_TYPOS:
        dirty.at[i, "exp_level"] = random.choice(EXP_TYPOS[lvl])

# 4. stray whitespace in title (~10% of rows)
ws_idx = np.random.choice(idx, size=int(n * 0.10), replace=False)
for i in ws_idx:
    dirty.at[i, "title"] = f"  {dirty.at[i, 'title']}  "

# 5. missing salary values (~3% of rows)
miss_idx = np.random.choice(idx, size=int(n * 0.03), replace=False)
dirty.loc[miss_idx, "salary_min"] = np.nan
dirty.loc[miss_idx, "salary_max"] = np.nan

# 6. impossible salaries (~0.5%)
bad_idx = np.random.choice(idx, size=int(n * 0.005), replace=False)
dirty.loc[bad_idx, "salary_min"] = -1
dirty.loc[bad_idx, "salary_max"] = 0

# 7. duplicate rows (~2.5%), whole rows including the id
dup_rows = dirty.sample(frac=0.025, random_state=2)
dirty = pd.concat([dirty, dup_rows], ignore_index=True)

dirty.to_csv(RAW, index=False)
print(f"  raw_dirty rows: {len(dirty):,}  (source had {len(df):,})")

# what is wrong with it
print("profiling raw data...")
profile = []
profile.append(f"Total rows in raw export        : {len(dirty):,}")
profile.append(f"Exact duplicate rows             : {dirty.duplicated().sum():,}")
profile.append(f"Missing salary_min               : {dirty['salary_min'].isna().sum():,}")
profile.append(f"Missing salary_max               : {dirty['salary_max'].isna().sum():,}")
profile.append(f"Negative/zero salary entries     : {(dirty['salary_min'] <= 0).sum():,}")
profile.append(f"Distinct country spellings       : {dirty['country'].nunique()} (should be 10)")
profile.append(f"Distinct exp_level spellings      : {dirty['exp_level'].nunique()} (should be 4)")
profile.append(f"Rows with leading/trailing space  : {(dirty['title'] != dirty['title'].str.strip()).sum():,}")
try:
    pd.to_datetime(dirty["posted_date"], format="%Y-%m-%d")
    bad_dates = 0
except Exception:
    bad_dates = (~dirty["posted_date"].str.match(r"^\d{4}-\d{2}-\d{2}$")).sum()
profile.append(f"Dates not in ISO yyyy-mm-dd format: {bad_dates:,}")

# cleaning
print("cleaning...")
clean = dirty.copy()
actions = []

# a) drop exact duplicate rows
before = len(clean)
clean = clean.drop_duplicates()
actions.append(f"Dropped {before - len(clean):,} exact duplicate rows")

# b) standardize country names
country_map = {}
for canon, variants in COUNTRY_VARIANTS.items():
    for v in variants:
        country_map[v.strip().lower()] = canon
clean["country"] = clean["country"].apply(
    lambda x: country_map.get(str(x).strip().lower(), str(x).strip())
)
actions.append(f"Standardized country names to {clean['country'].nunique()} canonical values "
               f"(was {dirty['country'].nunique()} distinct spellings)")

# c) standardize experience level
exp_map = {}
for canon, variants in EXP_TYPOS.items():
    for v in variants:
        exp_map[v.strip().lower()] = canon
clean["exp_level"] = clean["exp_level"].apply(
    lambda x: exp_map.get(str(x).strip().lower(), str(x).strip())
)
actions.append(f"Standardized exp_level to {clean['exp_level'].nunique()} canonical values "
               f"(was {dirty['exp_level'].nunique()} distinct spellings)")

# d) trim whitespace in title
ws_before = (clean["title"] != clean["title"].str.strip()).sum()
clean["title"] = clean["title"].str.strip()
actions.append(f"Trimmed stray whitespace on {ws_before:,} title values")

# e) parse all date formats to ISO yyyy-mm-dd
def parse_any_date(d):
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(d, format=fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return pd.NaT
non_iso_before = bad_dates
clean["posted_date"] = clean["posted_date"].apply(parse_any_date)
actions.append(f"Reparsed {non_iso_before:,} non-ISO dates (mixed dd-mm-yyyy / mm/dd/yyyy / dd/mm/yyyy) to yyyy-mm-dd")

# f) negative or zero salary: set to null instead of keeping it
invalid_sal = (clean["salary_min"] <= 0).sum()
clean.loc[clean["salary_min"] <= 0, ["salary_min", "salary_max"]] = np.nan
actions.append(f"Nulled {invalid_sal:,} impossible salary entries (<= 0) rather than keeping bad values")

# g) missing salary: fill with the median of the same country + experience level
missing_before = clean["salary_min"].isna().sum()
clean["salary_min"] = clean.groupby(["country","exp_level"])["salary_min"]\
    .transform(lambda s: s.fillna(s.median()))
clean["salary_max"] = clean.groupby(["country","exp_level"])["salary_max"]\
    .transform(lambda s: s.fillna(s.median()))
still_missing = clean["salary_min"].isna().sum()
actions.append(f"Imputed {missing_before - still_missing:,} missing salary values using the "
               f"country+experience-level median ({still_missing} left unresolved due to sparse group)")

clean.to_csv(OUT, index=False)

# check the result against the original file
print("validating against original source...")
qa = []
qa.append(f"Original clean source rows : {len(df):,}")
qa.append(f"Recovered cleaned rows     : {len(clean):,}")
qa.append(f"Row count match            : {'YES' if len(clean) == len(df) else 'NO - investigate'}")
qa.append(f"Countries match canonical set: {'YES' if set(clean['country'].unique()) <= set(df['country'].unique()) else 'NO'}")
qa.append(f"Exp levels match canonical set: {'YES' if set(clean['exp_level'].unique()) <= set(df['exp_level'].unique()) else 'NO'}")

# write the report
with open(REPORT, "w", encoding="utf-8") as f:
    f.write("DATA CLEANING REPORT - job_postings\n")
    f.write("=" * 60 + "\n")
    f.write("Note: the raw file is a simulated dirty copy made by data_cleaning.py.\n\n")
    f.write("1. ISSUES FOUND IN RAW DATA\n")
    f.write("-" * 60 + "\n")
    f.write("\n".join(profile) + "\n\n")
    f.write("2. CLEANING ACTIONS TAKEN\n")
    f.write("-" * 60 + "\n")
    for a in actions:
        f.write(f"- {a}\n")
    f.write("\n3. VALIDATION AGAINST ORIGINAL SOURCE\n")
    f.write("-" * 60 + "\n")
    f.write("\n".join(qa) + "\n")

print("\n".join(profile))
print()
print("\n".join(actions))
print()
print("\n".join(qa))
print(f"\nReport written to {REPORT}")
