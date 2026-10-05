# Power BI - Global AI Job Market Intelligence

> The data behind this is simulated (see the README). The KPI values quoted below come from the MySQL queries; check each visual against `facts.py` before taking screenshots.

---

## Data Import

**Option A: connect to MySQL (recommended).** Get Data → MySQL database → Server: `localhost`, Database: `job_market` → select the 5 tables. Power BI needs the MySQL Connector/NET driver installed; Import mode is fine for this data size. Load the database first with `load_mysql.py`.

**Option B: import the CSVs.** Get Data → Text/CSV → import all 5 files:

```
companies.csv
job_postings.csv
skills.csv
skill_demand.csv
salary_data.csv
```

---

## Relationships (Model view)

| From | To | Cardinality |
|---|---|---|
| companies[company_id] | job_postings[company_id] | 1:Many |
| job_postings[job_id] | skill_demand[job_id] | 1:Many |
| job_postings[job_id] | salary_data[job_id] | 1:Many |
| skills[skill_id] | skill_demand[skill_id] | 1:Many |
| skills[skill_id] | salary_data[key_skill_id] | 1:Many |

---

## Calculated Columns

Add these in the job_postings table:

```dax
Salary Midpoint = (job_postings[salary_min] + job_postings[salary_max]) / 2

Year Label = TEXT(job_postings[year], "0")
```

---

## DAX Measures

Create a blank table called _Measures and add everything here.

```dax
Total Postings = COUNTROWS(job_postings)

Total Companies = DISTINCTCOUNT(job_postings[company_id])

Total Countries = DISTINCTCOUNT(job_postings[country])

Skills Tracked = DISTINCTCOUNT(skill_demand[skill_name])

Skill Demand Rate =
DIVIDE(
    DISTINCTCOUNT(skill_demand[job_id]),
    CALCULATE(DISTINCTCOUNT(job_postings[job_id])),
    0
)

Python Demand 2021 =
CALCULATE(
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(skill_demand[job_id]), skill_demand[skill_name] = "Python"),
        CALCULATE(DISTINCTCOUNT(job_postings[job_id]), job_postings[year] = 2021)
    )
)

Python Demand 2025 =
CALCULATE(
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(skill_demand[job_id]), skill_demand[skill_name] = "Python"),
        CALCULATE(DISTINCTCOUNT(job_postings[job_id]), job_postings[year] = 2025)
    )
)

LLM APIs Demand 2025 =
CALCULATE(
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(skill_demand[job_id]), skill_demand[skill_name] = "LLM APIs"),
        CALCULATE(DISTINCTCOUNT(job_postings[job_id]), job_postings[year] = 2025)
    )
)

LLM APIs Demand 2021 =
CALCULATE(
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(skill_demand[job_id]), skill_demand[skill_name] = "LLM APIs"),
        CALCULATE(DISTINCTCOUNT(job_postings[job_id]), job_postings[year] = 2021)
    )
)

LLM APIs Relative Growth =
DIVIDE([LLM APIs Demand 2025] - [LLM APIs Demand 2021], [LLM APIs Demand 2021], 0)

VBA Demand 2025 =
CALCULATE(
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(skill_demand[job_id]), skill_demand[skill_name] = "VBA/Macros"),
        CALCULATE(DISTINCTCOUNT(job_postings[job_id]), job_postings[year] = 2025)
    )
)

AI Skill Premium Avg =
CALCULATE(AVERAGE(salary_data[premium_pct]), salary_data[premium_pct] > 0)

Top Skill Premium = MAX(salary_data[premium_pct])

Avg Salary Midpoint = AVERAGE(job_postings[Salary Midpoint])

Remote Rate =
DIVIDE(
    CALCULATE(COUNTROWS(job_postings), job_postings[remote_type] = "Remote"),
    [Total Postings], 0
)

Hybrid Rate =
DIVIDE(
    CALCULATE(COUNTROWS(job_postings), job_postings[remote_type] = "Hybrid"),
    [Total Postings], 0
)

Onsite Rate =
DIVIDE(
    CALCULATE(COUNTROWS(job_postings), job_postings[remote_type] = "Onsite"),
    [Total Postings], 0
)
```

---

## Page 1 - Executive Overview

**KPI Cards (top row):**
- Total Postings - value: `[Total Postings]`
- Countries - value: `[Total Countries]`
- Skills Tracked - value: `[Skills Tracked]`
- LLM APIs Growth - value: `[LLM APIs Relative Growth]` formatted as %
- AI Salary Premium - value: `[Top Skill Premium]` formatted as +%

**Visuals:**

Line chart - Top 5 skill demand trends 2021–2025
- X axis: job_postings[year]
- Y axis: `[Skill Demand Rate]`
- Legend: skill_demand[skill_name]
- Filter: skill_name IN (Python, SQL, LLM APIs, Excel, dbt)
- Line colours: Python=#FF6B35, SQL=#4ECDC4, LLM APIs=#F5C542, Excel=#6B6B90, dbt=#52C97F

Donut chart - Postings by country
- Values: `[Total Postings]`
- Legend: job_postings[country]
- Use distinct colours per country, no border

Bar chart - Postings by sector (2025)
- X axis: job_postings[sector]
- Y axis: `[Total Postings]`
- Filter: job_postings[year] = 2025
- Bar colour: #FF6B35

Table - Key skill summary
- Columns: skill_name, demand 2021, demand 2025, change pp, status
- Add conditional formatting on change column: positive=green, negative=red

**Slicers:** job_postings[year], job_postings[country], job_postings[sector]

---

## Page 2 - Skill Demand Intelligence

**Visuals:**

Clustered bar chart - Demand 2021 vs 2025 all skills
- X axis: skill_demand[skill_name] sorted by 2025 demand descending
- Y axis: `[Skill Demand Rate]`
- Series: job_postings[year] filtered to 2021 and 2025
- Colours: 2021=#6B6B90 (50% opacity), 2025=#FF6B35

Horizontal bar - Top 8 fastest growing skills
- Values: calculated column for (demand_2025 - demand_2021)
- Filter: change > 0, top 8 by change
- Bar colour: #52C97F

Horizontal bar - Fastest declining skills
- Same as above but filter: change < 0, bottom 6
- Bar colour: #F15B5B

Matrix - Skill × Year demand %
- Rows: skill_demand[skill_name]
- Columns: job_postings[year]
- Values: `[Skill Demand Rate]`
- Background colour rule: 0%=red, 50%=amber, 100%=green

**Slicers:** skills[category], job_postings[country]

---

## Page 3 - Country × Skill Heatmap

**KPI Cards:**
- Country with highest LLM APIs demand (USA - 66.2%)
- India LLM APIs 2025 (53.8%)
- USA vs India gap (+12.4pp)
- Most stable skill (SQL)

**Visuals:**

Matrix - Country × skill demand heatmap
- Rows: job_postings[country]
- Columns: skill_demand[skill_name]
- Filter skills: Python, SQL, LLM APIs, Machine Learning, Cloud (AWS/GCP/Azure), Power BI, dbt
- Values: `[Skill Demand Rate]`
- Background colour rule: 0%=red → 100%=teal/green
- Filter: job_postings[year] = 2025

Bar chart - Country ranking by LLM APIs demand
- X axis: job_postings[country]
- Y axis: `[Skill Demand Rate]` filtered to skill_name = "LLM APIs" and year = 2025
- Sort descending
- Use colour rule: top 3 = #FF6B35, rest = #4ECDC4

Line chart - USA vs India vs UK for Python and LLM APIs
- X axis: job_postings[year]
- Y axis: `[Skill Demand Rate]`
- Filter: country IN (USA, India, UK), skill_name IN (Python, LLM APIs)
- Use solid lines for USA, dashed for India and UK
- Colours: Python lines = #FF6B35 family, LLM APIs lines = #4ECDC4 family

**Slicers:** job_postings[year], skills[category]

---

## Page 4 - Salary & Remote Work

**KPI Cards:**
- Top Salary Premium (+22% - LLM APIs)
- Avg AI Premium (+17%)
- Hybrid Work 2025 (44.9%)
- Remote Work 2025 (18.7%)

**Visuals:**

Horizontal bar - Salary premium by AI skill
- Values: `[AI Skill Premium Avg]`
- Axis: skills[skill_name]
- Sort descending by premium
- Colour rule: ≥20% = #F5C542, ≥16% = #4ECDC4, else = #6B6B90

Scatter chart - Skill demand growth vs salary premium
- X axis: demand change 2021→2025 (pp)
- Y axis: `[AI Skill Premium Avg]`
- Size: `[Total Postings]` in 2025
- Details: skills[skill_name]
- This shows which skills offer both high growth and high pay

Stacked bar - Remote / Hybrid / Onsite trend
- X axis: job_postings[year]
- Y axis: count stacked by remote_type
- Colours: Remote=#FF6B35, Hybrid=#4ECDC4, Onsite=#6B6B90

Matrix - Country × Experience level salary midpoint
- Rows: job_postings[country]
- Columns: job_postings[exp_level] ordered Junior → Mid → Senior → Lead
- Values: `[Avg Salary Midpoint]`
- Background colour rule per row: scale from low to high within each country
- Filter: skill_name IN (Python, LLM APIs, Machine Learning), year = 2025

**Slicers:** job_postings[country], job_postings[exp_level]

---

## Formatting

| Element | Value |
|---|---|
| Page background | #1A1A2E |
| Card background | #16213E |
| Accent colour | #FF6B35 |
| Secondary colour | #4ECDC4 |
| Font | Segoe UI |
| Title size | 14pt |
| KPI value size | 28pt |
| Grid lines | off on x-axis, light on y-axis |
| Card border | 1px solid #252545 |
| Border radius | 4px |

---

## Export checklist

- [ ] Export all 4 pages as PNG (File → Export → Export to PDF → screenshot each page)
- [ ] Save .pbix to project folder
- [ ] Screenshot the model view for README
- [ ] Upload CSVs and .pbix to GitHub
