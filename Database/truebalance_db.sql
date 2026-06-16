-- ═══════════════════════════════════════════════════════════════
-- TRUEBALANCE DATABASE SETUP SCRIPT
-- Run this once to set up the full database for TrueBalance API
-- Compatible with MySQL 8.0+
-- ═══════════════════════════════════════════════════════════════

-- 1. CREATE DATABASE
-- ─────────────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS truebalance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE truebalance_db;

-- ═══════════════════════════════════════════════════════════════
-- 2. CREATE TABLES
-- ═══════════════════════════════════════════════════════════════

-- Expenses Table
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    date         DATE           NOT NULL,
    month        VARCHAR(10)    NOT NULL,
    category     VARCHAR(50)    NOT NULL,
    amount       DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_month    (month),
    INDEX idx_category (category),
    INDEX idx_date     (date)
);

-- Budgets Table
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budgets (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    month        VARCHAR(10)    NOT NULL UNIQUE,
    budget       DECIMAL(10, 2) NOT NULL CHECK (budget > 0),
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_month (month)
);

-- ═══════════════════════════════════════════════════════════════
-- 3. CREATE DEDICATED USER (Recommended over using root)
-- ═══════════════════════════════════════════════════════════════
-- Replace '123456789' with a strong password before running

CREATE USER IF NOT EXISTS 'Durvesh'@'localhost' IDENTIFIED BY '123456789';

GRANT SELECT, INSERT, UPDATE, DELETE ON truebalance_db.* TO 'Durvesh'@'localhost';

-- For production/cloud deployment (e.g. Railway, PlanetScale, AWS RDS)
-- replace 'localhost' with '%' to allow connections from any host:
-- CREATE USER IF NOT EXISTS 'Durvesh'@'%' IDENTIFIED BY '123456789';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON truebalance_db.* TO 'Durvesh'@'%';

FLUSH PRIVILEGES;

-- ═══════════════════════════════════════════════════════════════
-- 5. USEFUL VIEWS (for analytics / future dashboard features)
-- ═══════════════════════════════════════════════════════════════

-- Monthly spending summary vs budget
CREATE OR REPLACE VIEW monthly_summary AS
    SELECT
        b.month,
        b.budget                                     AS budget_limit,
        COALESCE(SUM(e.amount), 0)                   AS total_spent,
        b.budget - COALESCE(SUM(e.amount), 0)        AS remaining,
        CASE
            WHEN COALESCE(SUM(e.amount), 0) < b.budget THEN 'under'
            WHEN COALESCE(SUM(e.amount), 0) > b.budget THEN 'over'
            ELSE 'exact'
        END                                          AS status
    FROM budgets b
    LEFT JOIN expenses e ON b.month = e.month
    GROUP BY b.month, b.budget;

-- Category-wise spending per month
CREATE OR REPLACE VIEW category_monthly_breakdown AS
    SELECT
        month,
        category,
        COUNT(*)          AS num_transactions,
        SUM(amount)       AS total_amount,
        AVG(amount)       AS avg_amount
    FROM expenses
    GROUP BY month, category
    ORDER BY month, total_amount DESC;

-- ═══════════════════════════════════════════════════════════════
-- 6. VERIFY SETUP
-- ═══════════════════════════════════════════════════════════════

SHOW TABLES;
SELECT * FROM monthly_summary;