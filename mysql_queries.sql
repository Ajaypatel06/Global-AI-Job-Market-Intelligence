-- mysql_queries.sql: the 10 queries (MySQL 8.0+, they use CTEs)
-- run USE job_market; first

-- Q1: skill demand trend, 2021 to 2025

WITH yearly_totals AS (
    SELECT
        year,
        COUNT(DISTINCT job_id) AS total_jobs
    FROM job_postings
    GROUP BY year
),

skill_yearly AS (
    SELECT
        skill_name,
        year,
        COUNT(DISTINCT job_id) AS skill_jobs
    FROM skill_demand
    GROUP BY skill_name, year
)

SELECT
    sy.skill_name,
    sy.year,
    sy.skill_jobs,
    yt.total_jobs,

    ROUND(
        sy.skill_jobs * 100.0 / yt.total_jobs,
        1
    ) AS demand_pct

FROM skill_yearly sy
JOIN yearly_totals yt
    ON sy.year = yt.year

ORDER BY sy.skill_name, sy.year;



-- Q2: fastest growing skills

WITH demand AS (

    SELECT
        sd.skill_name,
        sk.category,

        ROUND(
            SUM(CASE WHEN sd.year = 2021 THEN 1 ELSE 0 END)
            * 100.0 /
            (SELECT COUNT(*) FROM job_postings WHERE year = 2021),
            1
        ) AS demand_2021,

        ROUND(
            SUM(CASE WHEN sd.year = 2025 THEN 1 ELSE 0 END)
            * 100.0 /
            (SELECT COUNT(*) FROM job_postings WHERE year = 2025),
            1
        ) AS demand_2025

    FROM skill_demand sd
    JOIN skills sk
        ON sd.skill_id = sk.skill_id

    GROUP BY sd.skill_name, sk.category
),

raw_demand AS (
    -- unrounded values, so relative growth isn't thrown off by the rounding
    SELECT
        sd.skill_name,
        SUM(CASE WHEN sd.year = 2021 THEN 1 ELSE 0 END) * 100.0
            / (SELECT COUNT(*) FROM job_postings WHERE year = 2021) AS raw_2021,
        SUM(CASE WHEN sd.year = 2025 THEN 1 ELSE 0 END) * 100.0
            / (SELECT COUNT(*) FROM job_postings WHERE year = 2025) AS raw_2025
    FROM skill_demand sd
    GROUP BY sd.skill_name
)

SELECT
    d.skill_name,
    d.category,
    d.demand_2021,
    d.demand_2025,

    ROUND(
        d.demand_2025 - d.demand_2021,
        1
    ) AS absolute_growth_pp,

    ROUND(
        (r.raw_2025 - r.raw_2021) / NULLIF(r.raw_2021, 0) * 100,
        0
    ) AS relative_growth_pct,

    CASE
        WHEN d.demand_2025 > d.demand_2021 * 1.5 THEN 'High Growth'
        WHEN d.demand_2025 > d.demand_2021 THEN 'Growing'
        WHEN d.demand_2025 < d.demand_2021 * 0.7 THEN 'Declining'
        ELSE 'Stable'
    END AS growth_status

FROM demand d
JOIN raw_demand r ON r.skill_name = d.skill_name
ORDER BY absolute_growth_pp DESC;



-- Q3: skill demand by country (2025)

WITH country_totals AS (

    SELECT
        country,
        COUNT(DISTINCT job_id) AS total_jobs
    FROM job_postings
    WHERE year = 2025
    GROUP BY country
),

country_skills AS (

    SELECT
        country,
        skill_name,
        COUNT(DISTINCT job_id) AS skill_jobs
    FROM skill_demand
    WHERE year = 2025
    GROUP BY country, skill_name
)

SELECT
    cs.country,
    cs.skill_name,
    cs.skill_jobs,
    ct.total_jobs,

    ROUND(
        cs.skill_jobs * 100.0 / ct.total_jobs,
        1
    ) AS demand_pct

FROM country_skills cs
JOIN country_totals ct
    ON cs.country = ct.country

WHERE cs.skill_name IN (
    'Python',
    'SQL',
    'LLM APIs',
    'Excel',
    'dbt',
    'Cloud (AWS/GCP/Azure)'
)

ORDER BY cs.skill_name, demand_pct DESC;



-- Q4: skill half-life index
-- straight-line model: annual_decline = (demand_2025 - demand_2021) / 4
-- half-life = demand_2021 / (2 * |annual_decline|), in years

WITH demand AS (

    SELECT
        skill_name,

        ROUND(
            SUM(CASE WHEN year = 2021 THEN 1 ELSE 0 END)
            * 100.0 /
            (SELECT COUNT(*) FROM job_postings WHERE year = 2021),
            2
        ) AS demand_2021,

        ROUND(
            SUM(CASE WHEN year = 2025 THEN 1 ELSE 0 END)
            * 100.0 /
            (SELECT COUNT(*) FROM job_postings WHERE year = 2025),
            2
        ) AS demand_2025

    FROM skill_demand
    GROUP BY skill_name
),

declining AS (

    SELECT
        skill_name,
        demand_2021,
        demand_2025,

        ROUND(
            (demand_2025 - demand_2021) / 4.0,
            3
        ) AS annual_decline

    FROM demand
    WHERE demand_2025 < demand_2021
)

SELECT
    skill_name,
    demand_2021,
    demand_2025,
    annual_decline,

    ROUND(
        -demand_2021 / (2 * annual_decline),
        1
    ) AS half_life_years,

    CASE
        WHEN (-demand_2021 / (2 * annual_decline)) < 5
            THEN 'Near Obsolete'

        WHEN (-demand_2021 / (2 * annual_decline)) < 10
            THEN 'Fading'

        ELSE 'Long Tail'
    END AS risk_level

FROM declining
WHERE annual_decline < 0

ORDER BY half_life_years ASC;



-- Q5: salary premium by skill

SELECT
    sk.skill_name,
    sk.category,

    COUNT(sd.salary_id) AS postings_count,

    ROUND(
        AVG(sd.premium_pct),
        1
    ) AS avg_premium_pct,

    ROUND(
        AVG(sd.salary_min),
        0
    ) AS avg_salary_min,

    ROUND(
        AVG(sd.salary_max),
        0
    ) AS avg_salary_max,

    ROUND(
        AVG((sd.salary_min + sd.salary_max) / 2),
        0
    ) AS avg_mid_salary

FROM salary_data sd
JOIN skills sk
    ON sd.key_skill_id = sk.skill_id

GROUP BY sk.skill_name, sk.category

ORDER BY avg_premium_pct DESC;



-- Q6: remote work trend

SELECT
    year,

    COUNT(*) AS total_jobs,

    SUM(CASE WHEN remote_type = 'Remote' THEN 1 ELSE 0 END)
        AS remote_jobs,

    SUM(CASE WHEN remote_type = 'Hybrid' THEN 1 ELSE 0 END)
        AS hybrid_jobs,

    SUM(CASE WHEN remote_type = 'Onsite' THEN 1 ELSE 0 END)
        AS onsite_jobs,

    ROUND(
        SUM(CASE WHEN remote_type = 'Remote' THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*),
        1
    ) AS remote_pct,

    ROUND(
        SUM(CASE WHEN remote_type = 'Hybrid' THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*),
        1
    ) AS hybrid_pct,

    ROUND(
        SUM(CASE WHEN remote_type = 'Onsite' THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*),
        1
    ) AS onsite_pct

FROM job_postings

GROUP BY year
ORDER BY year;



-- Q7: skill co-occurrence

SELECT
    a.skill_name AS primary_skill,
    b.skill_name AS paired_skill,

    COUNT(*) AS co_occurrences,

    ROUND(
        COUNT(*) * 100.0 /
        (
            SELECT COUNT(DISTINCT job_id)
            FROM job_postings
            WHERE year = 2025
        ),
        1
    ) AS pct_of_jobs

FROM skill_demand a

JOIN skill_demand b
    ON a.job_id = b.job_id
   AND a.skill_id < b.skill_id

WHERE a.year = 2025
  AND b.year = 2025

GROUP BY
    a.skill_name,
    b.skill_name

ORDER BY co_occurrences DESC
LIMIT 15;



-- Q8: sector x skill category matrix (2025)
-- % of postings that need at least one skill from the category.
-- DISTINCT job_id matters, otherwise a posting with 3 AI skills is counted 3 times and the % goes over 100

WITH sector_totals AS (

    SELECT
        sector,
        COUNT(DISTINCT job_id) AS total_jobs
    FROM job_postings
    WHERE year = 2025
    GROUP BY sector
)

SELECT
    jp.sector,
    st.total_jobs,

    ROUND(
        COUNT(DISTINCT CASE WHEN sk.category = 'AI/ML' THEN jp.job_id END)
        * 100.0 / st.total_jobs,
        1
    ) AS ai_ml_pct,

    ROUND(
        COUNT(DISTINCT CASE WHEN sk.category = 'Programming' THEN jp.job_id END)
        * 100.0 / st.total_jobs,
        1
    ) AS programming_pct,

    ROUND(
        COUNT(DISTINCT CASE WHEN sk.category = 'Visualization' THEN jp.job_id END)
        * 100.0 / st.total_jobs,
        1
    ) AS visualization_pct,

    ROUND(
        COUNT(DISTINCT CASE WHEN sk.category = 'Cloud' THEN jp.job_id END)
        * 100.0 / st.total_jobs,
        1
    ) AS cloud_pct

FROM job_postings jp

JOIN skill_demand sd
    ON jp.job_id = sd.job_id

JOIN skills sk
    ON sd.skill_id = sk.skill_id

JOIN sector_totals st
    ON jp.sector = st.sector

WHERE jp.year = 2025

GROUP BY jp.sector, st.total_jobs

ORDER BY ai_ml_pct DESC;



-- Q9: emerging skill radar

WITH skills_2023 AS (

    SELECT
        skill_name,
        COUNT(DISTINCT job_id) AS jobs_2023
    FROM skill_demand
    WHERE year = 2023
    GROUP BY skill_name
),

skills_2025 AS (

    SELECT
        skill_name,
        COUNT(DISTINCT job_id) AS jobs_2025
    FROM skill_demand
    WHERE year = 2025
    GROUP BY skill_name
)

SELECT
    s25.skill_name,

    ROUND(
        s23.jobs_2023 * 100.0 /
        (SELECT COUNT(*) FROM job_postings WHERE year = 2023),
        1
    ) AS demand_2023_pct,

    ROUND(
        s25.jobs_2025 * 100.0 /
        (SELECT COUNT(*) FROM job_postings WHERE year = 2025),
        1
    ) AS demand_2025_pct,

    ROUND(
        (
            (
                s25.jobs_2025 * 1.0 /
                (SELECT COUNT(*) FROM job_postings WHERE year = 2025)
            )
            -
            (
                s23.jobs_2023 * 1.0 /
                (SELECT COUNT(*) FROM job_postings WHERE year = 2023)
            )
        ) * 100,
        1
    ) AS percentage_point_growth

FROM skills_2025 s25

LEFT JOIN skills_2023 s23
    ON s25.skill_name = s23.skill_name

ORDER BY percentage_point_growth DESC
LIMIT 10;



-- Q10: country x experience salary benchmark (2025)
-- postings that need Python, LLM APIs or Machine Learning. EXISTS so each posting counts once
-- (a plain join repeats postings that list more than one of these skills)

SELECT
    jp.country,
    jp.exp_level,

    COUNT(*) AS total_jobs,

    ROUND(AVG(jp.salary_min), 0) AS avg_salary_min,

    ROUND(AVG(jp.salary_max), 0) AS avg_salary_max,

    ROUND(AVG((jp.salary_min + jp.salary_max) / 2.0), 0) AS avg_mid_salary

FROM job_postings jp

WHERE jp.year = 2025
  AND EXISTS (
        SELECT 1
        FROM skill_demand sd
        WHERE sd.job_id = jp.job_id
          AND sd.skill_name IN ('Python', 'LLM APIs', 'Machine Learning')
  )

GROUP BY
    jp.country,
    jp.exp_level

ORDER BY
    jp.country,

    CASE jp.exp_level
        WHEN 'Junior' THEN 1
        WHEN 'Mid' THEN 2
        WHEN 'Senior' THEN 3
        WHEN 'Lead' THEN 4
        ELSE 5
    END;
