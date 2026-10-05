# Interview Q&A - Global AI Job Market Intelligence
*Private prep file. Do not publish it on GitHub. Every number below was recomputed from the generated data.*

### Q1. Walk me through this project.

> "I built a market-intelligence pipeline on a MySQL database holding a simulated dataset of 50,000 job postings, 500 companies, 10 countries and 25 skills from 2021 to 2025. I was upfront that it's simulated, because I wanted real control over the ground truth so I could test whether my analysis recovers it.
>
> I designed a 5-table relational schema (companies, job_postings, skills, skill_demand, salary_data), generated 440,904 skill-to-posting records, then wrote 10 SQL queries, 6 Python charts, a skill half-life index, an interactive dashboard and a Power BI build guide.
>
> On that data the analysis recovers: Python 46.0% to 91.3%, LLM APIs 1.1% to 58.6%, VBA falling from 31.0% to 7.8%, and SQL flat near 88.0–89.5%."

---

### Q2. What is a skill half-life and how did you calculate it?

> "It's the number of years for a skill's demand to fall to half of its 2021 level, if it keeps falling at the rate I observed from 2021 to 2025. The formula is annual change = (demand 2025 minus demand 2021) divided by 4, then half-life = demand 2021 divided by twice the absolute annual change.
>
> VBA went from 31.0% to 7.8%, about 5.8 points a year, so its half-life is 2.7 years. Excel fell from 92.7% to 69.2%, a similar yearly drop from a much higher base, so its half-life is 7.9 years.
>
> It's a linear, two-endpoint model, so it's a planning heuristic, not a forecast. An exponential model would give different numbers (about 2 years for VBA, for example)."

---

### Q3. How did you handle the country dimension?

> "In the generator each country has a multiplier on AI/ML and data-engineering skill demand, for example the USA at 1.15 and India at 0.95. That's an assumption I set, not an observed fact, and I say so in the README.
>
> In SQL I built a country_totals CTE (total postings per country in 2025), joined it to skill counts, and divided to get demand percentages. In 2025 that gives LLM APIs at 66.2% in the USA, 64.1% in Singapore and 53.8% in India, a 12.4-point gap. The heatmap shows it visually."

---

### Q4. What story does the data tell about Excel?

> "Excel went from 92.7% to 69.2% of postings. It's still among the most-required skills, but it's no longer a differentiator. So I'd read it as 'declining, not dying': a baseline requirement you maintain but don't lead with, while Python, SQL depth and LLM tooling differentiate."

---

### Q5. How did you structure the skill_demand table and why?

> "skill_demand is a junction table resolving the many-to-many between job_postings and skills. One row means one skill appearing in one posting. That lets me answer 'what percentage of 2025 postings require Python' with a COUNT(DISTINCT job_id), and find skill pairs with a self-join.
>
> The alternative, comma-separated skills in one column, turns every query into string parsing. I also denormalised year and country onto the junction rows to avoid joining back to job_postings on the hottest queries, and I added an index on job_id because without it the EXISTS and self-join queries were very slow."

---

### Q6. What does your fastest-growing-skills query look like?

> "A CTE computes each skill's demand rate in 2021 and 2025. The key detail is the denominator: you divide by total postings in that year, not by total skill rows. Then it computes percentage-point change and relative change, and a CASE statement labels each skill: more than 1.5x its 2021 level is 'High Growth', below 70% of its 2021 level is 'Declining'."

---

### Q7. Why 10 countries and not just India?

> "Comparing countries is part of the analysis, and a single-country dataset can't show differences between markets. The caveat is that the country differences in my data come from multipliers I set, so the comparison demonstrates the method. A real version would use observed postings per country."

---

### Q8. How would this look in a real company?

> "I'd replace the generator with a postings feed (an API or a scraping layer) and replace the probabilistic skill assignment with NLP extraction from job-description text, then run it on a managed MySQL instance (or PostgreSQL / BigQuery) with a scheduled refresh. The SQL and the dashboard structure would stay the same."

---

### Q9. What's your most interesting SQL query?

> "The co-occurrence query: skill_demand joined to itself on job_id with `a.skill_id < b.skill_id` so each pair is counted once. In 2025 Python and SQL appear together in 81.9% of postings, Python with Pandas/NumPy in 63.7%, Python with LLM APIs in 53.6%, and SQL with LLM APIs in 52.6%.
>
> I also found and fixed two bugs in my own queries: a sector matrix that counted skill rows instead of distinct postings and so could exceed 100%, and a salary benchmark whose join repeated postings once per matching skill and over-weighted them in the averages."

---

### Q10. How did you build the salary premium analysis?

> "To be precise: the premium is an input, not an estimate. Each AI/ML skill has a fixed premium in the generator, from LLM APIs at 22% down to Airflow at 13%. salary_data stores a posting's salary range and the premium of its highest-premium AI skill. In SQL I average premium_pct by skill, which just returns those constants.
>
> The analysis shows how I'd structure and visualise a premium analysis. With real data I'd estimate the premium by regressing salary on skills while controlling for country, experience and sector."

---

### Q11. What would you add with another week?

> "First, a real extraction pipeline on actual job-description text (spaCy or regex rules) to replace the generator. Second, a forecasting step for each skill's demand curve with confidence intervals. Third, a working filter layer on the dashboard, so someone can pick a country or skill and see trend, half-life and premium together."

---

### Q12. How does this connect to your other work?

> "My AI SaaS project found that LLM API feature users retained better and the rewrite feature was the biggest churn-reducer. This project looks at the hiring side of the same trend. Together they cover product analytics and market-intelligence analytics."
*(Check the exact retention figure against your other project before quoting it. I haven't verified it.)*

---

### Q13. Is the data real?

> "No, it's simulated, and the README says so on the first screen. I generated it so I'd know the ground truth. I set assumed demand curves, country multipliers and salary premiums, then checked that my SQL and charts recover them. The deliverable is the pipeline, the modelling and the analysis. It isn't a claim about the actual job market."

---

## NUMBERS TO MEMORISE

| Metric | Value |
|---|---|
| Postings / companies / countries / skills | 50,000 / 500 / 10 / 25 |
| Skill demand records | 440,904 |
| Python 2021 → 2025 | 46.0% → 91.3% |
| LLM APIs 2021 → 2025 | 1.1% → 58.6% (+5,323% relative) |
| SQL 2021 → 2025 | 88.0% → 89.5% |
| Excel 2021 → 2025 | 92.7% → 69.2% |
| VBA 2021 → 2025 | 31.0% → 7.8% |
| dbt 2021 → 2025 | 2.1% → 30.1% |
| Half-life (linear): VBA / SAS / MATLAB / R / Excel | 2.7 / 3.9 / 4.2 / 5.6 / 7.9 years |
| LLM APIs salary premium (input) | +22% |
| USA vs India LLM APIs (2025) | 66.2% vs 53.8% (gap 12.4pp) |
| Python + SQL co-occurrence (2025) | 81.9% |
| Hybrid / onsite / remote (2025) | 44.9% / 36.4% / 18.7% |
