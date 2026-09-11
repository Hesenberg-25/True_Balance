-- ═══════════════════════════════════════════════════════════════
-- TRUEBALANCE DATABASE SETUP SCRIPT (SANITIZED)
-- Run this once to set up the full database for TrueBalance API
-- NOTE: This file has been sanitized for public distribution.
-- Do NOT store passwords or credentials in this file. Create users/credentials
-- via your database provider (Neon, RDS, PlanetScale, etc.) and set them
-- using environment variables (DATABASE_URL) or secrets in your deploy platform.
-- Compatible with MySQL 8.0+ (adjust types for Postgres if you use Postgres)
-- ═══════════════════════════════════════════════════════════════

-- User accounts. Passwords are stored as salted PBKDF2 hashes by the API.
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE DATABASE IF NOT EXISTS truebalance_db;

USE truebalance_db;

-- ═══════════════════════════════════════════════════════════════
-- 2. CREATE TABLES
-- ═══════════════════════════════════════════════════════════════

-- User accounts
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expenses Table
CREATE TABLE IF NOT EXISTS expenses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT            NULL,
    date         DATE           NOT NULL,
    month        VARCHAR(10)    NOT NULL,
    category     VARCHAR(50)    NOT NULL,
    amount       DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_category (category),
    INDEX idx_date     (date),
    INDEX idx_expenses_user (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT            NULL,
    month        VARCHAR(10)    NOT NULL,
    budget       DECIMAL(10, 2) NOT NULL CHECK (budget > 0),
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_month (month),
    UNIQUE KEY idx_user_month (user_id, month),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ═══════════════════════════════════════════════════════════════
-- NOTE: User creation / credential setup removed for security.
-- Do NOT add production credentials (passwords, keys) into repository files.
-- Create database users and grant privileges using your DB provider or
-- administrative interface. Example (run as admin on your DB host) —
--   CREATE USER 'your_user'@'%' IDENTIFIED BY 'strong_password';
--   GRANT SELECT, INSERT, UPDATE, DELETE ON truebalance_db.* TO 'your_user'@'%';
-- For managed Postgres providers (Neon, Heroku), create users in the
-- provider dashboard and use the provided DATABASE_URL in your app env vars.
-- ═══════════════════════════════════════════════════════════════

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
-- Verify setup
-- ═══════════════════════════════════════════════════════════════

SHOW TABLES;
SELECT * FROM monthly_summary;
