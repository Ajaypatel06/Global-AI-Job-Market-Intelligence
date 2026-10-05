-- mysql_schema.sql  (MySQL 8.0+)
-- Creates the job_market database and the 5 tables.
-- Run this first, or let load_mysql.py run it for you.

CREATE DATABASE IF NOT EXISTS job_market
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE job_market;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS salary_data;
DROP TABLE IF EXISTS skill_demand;
DROP TABLE IF EXISTS job_postings;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS companies;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE companies (
    company_id    INT          NOT NULL,
    company_name  VARCHAR(100) NOT NULL,
    country       VARCHAR(30)  NOT NULL,
    sector        VARCHAR(30)  NOT NULL,
    size          VARCHAR(20)  NOT NULL,
    founded_year  SMALLINT     NOT NULL,
    PRIMARY KEY (company_id)
) ENGINE=InnoDB;

CREATE TABLE skills (
    skill_id    INT         NOT NULL,
    skill_name  VARCHAR(40) NOT NULL,
    category    VARCHAR(30) NOT NULL,
    PRIMARY KEY (skill_id),
    UNIQUE KEY uq_skill_name (skill_name)
) ENGINE=InnoDB;

CREATE TABLE job_postings (
    job_id       INT         NOT NULL,
    company_id   INT         NOT NULL,
    title        VARCHAR(60) NOT NULL,
    country      VARCHAR(30) NOT NULL,
    sector       VARCHAR(30) NOT NULL,
    exp_level    VARCHAR(10) NOT NULL,
    remote_type  VARCHAR(10) NOT NULL,
    posted_date  DATE        NOT NULL,
    year         SMALLINT    NOT NULL,
    salary_min   INT         NOT NULL,
    salary_max   INT         NOT NULL,
    PRIMARY KEY (job_id),
    KEY idx_jp_year (year),
    KEY idx_jp_country_year (country, year),
    KEY idx_jp_company (company_id),
    CONSTRAINT fk_jp_company FOREIGN KEY (company_id) REFERENCES companies (company_id)
) ENGINE=InnoDB;

-- junction table: one row = one skill required by one posting
CREATE TABLE skill_demand (
    demand_id   INT         NOT NULL,
    job_id      INT         NOT NULL,
    skill_id    INT         NOT NULL,
    skill_name  VARCHAR(40) NOT NULL,
    year        SMALLINT    NOT NULL,
    country     VARCHAR(30) NOT NULL,
    sector      VARCHAR(30) NOT NULL,
    PRIMARY KEY (demand_id),
    KEY idx_sd_job (job_id),
    KEY idx_sd_year_skill_job (year, skill_name, job_id),
    KEY idx_sd_skill (skill_id),
    CONSTRAINT fk_sd_job   FOREIGN KEY (job_id)   REFERENCES job_postings (job_id),
    CONSTRAINT fk_sd_skill FOREIGN KEY (skill_id) REFERENCES skills (skill_id)
) ENGINE=InnoDB;

CREATE TABLE salary_data (
    salary_id     INT          NOT NULL,
    job_id        INT          NOT NULL,
    key_skill_id  INT          NOT NULL,
    salary_min    INT          NOT NULL,
    salary_max    INT          NOT NULL,
    premium_pct   DECIMAL(5,1) NOT NULL,
    year          SMALLINT     NOT NULL,
    country       VARCHAR(30)  NOT NULL,
    PRIMARY KEY (salary_id),
    KEY idx_sal_job (job_id),
    KEY idx_sal_skill (key_skill_id),
    CONSTRAINT fk_sal_job   FOREIGN KEY (job_id)       REFERENCES job_postings (job_id),
    CONSTRAINT fk_sal_skill FOREIGN KEY (key_skill_id) REFERENCES skills (skill_id)
) ENGINE=InnoDB;
