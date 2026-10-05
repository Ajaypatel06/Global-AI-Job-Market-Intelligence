# Global AI Job Market Intelligence

I wanted to see how demand for data skills changed between 2021 and 2025, and whether newer skills like LLM APIs show up in salary. I couldn't find a free dataset that covers this, so the data comes from a script (`job_generator.py`) using trends I set myself. So the numbers below show that my SQL and charts pick up what I put in. They are not findings about the real job market.

Ajay Patel, Mumbai. [github.com/Ajaypatel06](https://github.com/Ajaypatel06)

## What's in the repo

- 50,000 job postings, 500 companies, 10 countries, 25 skills, 2021 to 2025, in a MySQL database with 5 tables
- 10 SQL queries in `mysql_queries.sql`
- 6 charts made with Python (matplotlib and seaborn)
- a half-life number for skills whose demand is falling
- an HTML dashboard and a Power BI build guide (the Power BI file itself is not finished)
- a small script that dirties the data and cleans it again, to practise the cleaning steps

## What the analysis gives

Python goes from 46.0% of postings in 2021 to 91.3% in 2025. LLM APIs goes from 1.1% to 58.6%, the biggest jump of any skill. SQL stays flat at about 88-89.5%. Excel drops from 92.7% to 69.2% and VBA from 31.0% to 7.8%. dbt goes from 2.1% to 30.1%.

By country in 2025, LLM APIs demand is highest in the USA (66.2%) and India is at 53.8%. That gap comes from a country multiplier I put in the generator, so it is not a real adoption gap. Hybrid roles overtake onsite: in 2025 it is 44.9% hybrid, 36.4% onsite and 18.7% remote (onsite was 60.6% in 2021). Remote peaks at 21.6% in 2023.

The salary premiums (LLM APIs +22%, Deep Learning +20%, down to Airflow +13%) are fixed numbers in the generator, so the salary chart just reads them back.

Python and SQL show up together in 81.9% of 2025 postings, Python and LLM APIs in 53.6%.

### Half-life

I defined half-life as the number of years until a skill's demand falls to half of its 2021 level, if it keeps dropping at the 2021-2025 pace:

```
annual_change = (demand_2025 - demand_2021) / 4
half_life = demand_2021 / (2 * |annual_change|)
```

| Skill | 2021 | 2025 | Half-life (years) |
|---|---|---|---|
| VBA/Macros | 31.0% | 7.8% | 2.7 |
| SAS | 23.0% | 11.3% | 3.9 |
| MATLAB | 12.2% | 6.4% | 4.2 |
| R | 29.0% | 18.6% | 5.6 |
| Excel | 92.7% | 69.2% | 7.9 |
| Alteryx | 18.8% | 14.2% | 8.3 |

It is a straight line through two points, so treat it as a rough guide.

## Running it

You need Python 3.9+ and MySQL 8.0+ (the queries use CTEs).

```bash
pip install -r requirements.txt

python job_generator.py     # writes the CSVs to data/
python load_mysql.py        # creates the job_market database and loads the CSVs
python analysis.py          # runs the SQL and saves the charts to charts/
python facts.py             # prints the headline numbers from the SQL
python data_cleaning.py     # optional, takes a few minutes
```

The scripts read the MySQL password from the `MYSQL_PASSWORD` environment variable and ask for it if it isn't set. `MYSQL_USER`, `MYSQL_HOST` and `MYSQL_PORT` also work (defaults: root, localhost, 3306).

On Windows: `set MYSQL_PASSWORD=yourpassword` in cmd, or `$env:MYSQL_PASSWORD="yourpassword"` in PowerShell.

To try the queries by hand, open `mysql_queries.sql` in MySQL Workbench, run `USE job_market;` and run them one at a time. The dashboard is a plain HTML file, open it in a browser.

## Notes

- `skill_demand` has one row per skill per posting. The composite index on `(year, skill_name, job_id)` is what keeps the self-join in Q7 fast.
- Q8 and Q10 used to give wrong results (percentages over 100%, and salary averages weighted by how many skills a posting lists). The fix was `COUNT(DISTINCT job_id)` in Q8 and an `EXISTS` in Q10.
- The cleaning script starts with 51,250 rows after adding noise and ends with the original 50,000 (1,250 duplicates removed, dates and spellings standardised, missing salaries filled with the country and level median). The details are in `charts/data_cleaning_report.txt`.
- Half-life uses only two points per skill, and the premiums and country gaps are assumptions. A real version would need real postings and a skill extractor.
