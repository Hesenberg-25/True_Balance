---
title: TrueBalance API
emoji: money_with_wings
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
---

# TrueBalance: Financial Analytics & Management Engine

![Markdown](https://img.shields.io/badge/markdown-%23000000.svg?style=for-the-badge&logo=markdown&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) ![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white) ![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![NodeJS](https://img.shields.io/badge/node.js-6DA55F?style=for-the-badge&logo=node.js&logoColor=white) ![Radix UI](https://img.shields.io/badge/radix%20ui-161618.svg?style=for-the-badge&logo=radix-ui&logoColor=white) ![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white) ![MySQL](https://img.shields.io/badge/mysql-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

TrueBalance is a full-stack personal finance application engineered to bridge the gap between daily expense tracking and long-term wealth forecasting. It combines a secure relational ledger with a modern frontend to make finance management simple and practical.

- 100% Transaction Ledgering: Safely records every inflow and outflow with zero data loss, using optimized database indexing for instant categorical filtering (Food, Utilities, Education).
- Proactive Budget Guard: Continuously computes aggregate monthly spending against customizable limits, delivering real-time variance metrics to actively prevent overruns.
- Precision Forecasting Matrix: Packed with integrated calculations providing mathematically exact projections for SIPs, compounding assets, progressive tax slabs, and amortized loan schedules.

## Features

### Expense Tracking
- **Add Expenses**: Log daily expenses across 7 predefined categories
  - Food
  - Transport
  - Household
  - Education
  - Health
  - Utilities
  - Other
- **View All Expenses**: See complete expense history with date, category, and amount
- **Filter by Category**: Get detailed breakdown of spending by category
- **Edit/Delete Expenses**: Modify or remove incorrect entries

### Budget Management
- **Set Monthly Budgets**: Define spending limits for each month
- **Budget vs Actual**: Real-time comparison of actual spending vs budgeted amount
- **Smart Alerts**: Get notifications when you're:
  - Under budget (with remaining balance)
  - Over budget (with overspend amount)
  - Exactly on budget
- **View All Budgets**: See all your monthly budget allocations

### Financial Calculators
- **Simple Interest Calculator**: Calculate interest earned on savings
- **Compound Interest Calculator**: Compute returns with different compounding frequencies
- **Loan Amortization**: Generate detailed EMI schedules with payment breakdown
- **Income Tax Calculator**: Calculate tax based on Indian tax brackets with slabs breakdown
- **SIP Calculator**: Plan Systematic Investment Plan returns

## Tech Stack

- **Frontend**: TypeScript, Next.js, React 19, TailwindCSS, Radix UI
- **Backend**: Python, FastAPI
- **Database**: MySQL
- **UI Components**: Radix UI with custom styling

## Project Structure

```text
True_Balance/
├── Frontend/          # Next.js React application
├── Backend/           # FastAPI Python backend
├── Database/          # MySQL database schema
├── .env.example       # Environment variable template
└── Makefile           # Local developer convenience commands
```

## Getting Started

### Prerequisites
- **Node.js 22+** (pinned via `.nvmrc` and `Frontend/package.json` engines)
- **Python 3.8+**
- **MySQL 8.0+**

### 1) Clone and install dependencies

```bash
git clone https://github.com/Hesenberg-25/True_Balance.git
cd True_Balance

# Backend deps
cd Backend
pip install -r requirements.txt
cd ..

# Frontend deps
cd Frontend
npm install
cd ..
```

> Tip: If you use `nvm`, run `nvm use` from repo root first.

### 2) Configure environment variables (Backend/.env)

The backend calls `load_dotenv()` from `Backend/main.py`, so place the env file at:

```text
Backend/.env
```

Create it from the root template:

```bash
cp .env.example Backend/.env
```

Then edit `Backend/.env` with your PostgreSQL connection URL:

```dotenv
DATABASE_URL=postgresql://username:password@host:5432/database
```

### 3) Create database

Create a free PostgreSQL database with Neon and copy its pooled connection string into `DATABASE_URL`. The API creates its required tables on startup.

### 4) Run backend

```bash
cd Backend
python main.py
```

Backend runs on `http://localhost:8000`

### 5) Run frontend

```bash
cd Frontend
npm run dev
```

Frontend runs on `http://localhost:3000`

## Free deployment

The recommended free setup is Vercel for the Next.js frontend, Render for the FastAPI backend, and Neon for PostgreSQL.

1. Push the repository to GitHub.
2. Create a Neon Free project and copy its pooled PostgreSQL connection string.
3. In Render, create a Blueprint from the repository. The included `render.yaml` creates the API service. Set `DATABASE_URL` to the Neon connection string.
4. Deploy the API and copy its public URL, for example `https://truebalance-api.onrender.com`.
5. In Vercel, import the repository and set the project root directory to `Frontend`.
6. Add the Vercel environment variable `NEXT_PUBLIC_API_URL` with the Render API URL.
7. Copy the final Vercel URL into Render's `FRONTEND_URL` environment variable, redeploy the API, and test `/api/health`.

Render Free services sleep after inactivity, so the first request can take about a minute. Neon Free provides persistent PostgreSQL storage; Render's local filesystem is ephemeral.

## One-command developer helpers (optional)

Use root `Makefile` commands:

```bash
make setup          # Installs backend + frontend dependencies
make setup-env      # Copies .env.example to Backend/.env (if missing)
make db-bootstrap   # Imports Database/truebalance_db.sql into your DATABASE
make dev-backend    # Runs backend
make dev-frontend   # Runs frontend
```

## API Endpoints

### Health Check
- `GET /api/health` - Check API status

### Expenses
- `POST /api/expenses` - Add new expense
- `GET /api/expenses` - Get all expenses
- `GET /api/expenses/category/{cat_name}` - Get expenses by category
- `PUT /api/expenses/{expense_id}` - Update expense
- `DELETE /api/expenses/{expense_id}` - Delete expense

### Budgets
- `POST /api/budgets` - Set/update monthly budget
- `GET /api/budgets` - Get all budgets
- `GET /api/budgets/check/{month_name}` - Check budget vs actual expenses

### Calculators
- `POST /api/calculator/simple-interest` - Simple interest calculation
- `POST /api/calculator/compound-interest` - Compound interest calculation
- `POST /api/calculator/loan-amortization` - Loan EMI schedule
- `POST /api/calculator/taxation` - Income tax calculation
- `POST /api/calculator/sip` - SIP returns calculation

## Sample API Requests

### Add Expense
```bash
curl -X POST http://localhost:8000/api/expenses \
  -F "category_name=Food" \
  -F "amount=500"
```

### Set Budget
```bash
curl -X POST http://localhost:8000/api/budgets \
  -F "month_idx=6" \
  -F "budget=50000"
```

### Calculate Compound Interest
```bash
curl -X POST http://localhost:8000/api/calculator/compound-interest \
  -F "principal=100000" \
  -F "rate=8" \
  -F "years=5" \
  -F "frequency=4"
```

## CORS Configuration

The API is configured with CORS enabled for all origins during development. Update this in production for security.

---

**Made by Hesenberg-25**
