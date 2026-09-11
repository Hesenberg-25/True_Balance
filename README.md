# TrueBalance: Financial Analytics & Management Engine

![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) ![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white) ![Render](https://img.shields.io/badge/Render-%46E3B7.svg?style=for-the-badge&logo=render&logoColor=white) ![Next JS](https://img.shields.io/badge/Next-black?style=for-the-badge&logo=next.js&logoColor=white) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white) ![Radix UI](https://img.shields.io/badge/radix%20ui-161618.svg?style=for-the-badge&logo=radix-ui&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

TrueBalance is a full-stack personal finance application engineered to bridge the gap between daily expense tracking and long-term wealth forecasting. It combines a secure relational ledger with a modern frontend to make finance management simple and practical.

- 100% Transaction Ledgering: Safely records every inflow and outflow with zero data loss, using optimized database indexing for instant categorical filtering (Food, Utilities, Education).
- Proactive Budget Guard: Continuously computes aggregate monthly spending against customizable limits, delivering real-time variance metrics to actively prevent overruns.
- Precision Forecasting Matrix: Packed with integrated calculations providing mathematically exact projections for SIPs, compounding assets, progressive tax slabs, and amortized loan schedules.

## Features

### Authentication & Security

What it does
- Each user has an account (email + password). All expenses/budgets are private to that account.
- Passwords are stored securely (PBKDF2 hash). Login creates a signed session cookie.

Where it lives
- Backend: Backend/main.py
  - POST /api/auth/signup, /api/auth/login, /api/auth/logout, GET /api/auth/me
- Frontend: login/signup forms under Frontend/app

How it works
1. Sign up → server stores a salted PBKDF2 hash (not the plain password).  
2. Login → server issues an HMAC‑signed cookie with your user id and expiry.  
3. Protected endpoints (expenses, budgets) require that cookie.

Quick production checklist
- Set a strong SESSION_SECRET in your secrets manager.  
- Serve over HTTPS and set cookies secure=True.  
- Restrict CORS to your frontend domain.  
Where it's implemented
- Backend: `Backend/main.py` contains auth endpoints:
  - POST `/api/auth/signup` — create an account and issue session cookie
  - POST `/api/auth/login` — authenticate and issue session cookie
  - POST `/api/auth/logout` — delete session cookie
  - GET  `/api/auth/me` — return current user's email (requires cookie)
- Frontend: Login/signup UI in `Frontend/app` uses form posts to these endpoints and stores no secrets client-side.

Why this approach
- Per-user scoping keeps financial data private and ensures a single source of truth.
- PBKDF2 with a strong salt and iterations defends against offline password cracking.
- Signed cookies avoid storing session state server-side while still allowing integrity checks; HTTPS and secure cookie flags enforce transport security in production.

Security recommendations
- Rotate `SESSION_SECRET` regularly and use a secrets manager for production hosts.
- Serve backend over HTTPS; set `secure=True` for cookies in production.
- Restrict CORS to the frontend domain(s) when deploying.
- Consider adding rate limiting on auth endpoints and email verification for signup.

---

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

When to use
- Record transactions immediately after spending (or when income arrives).
- Use filters and history when reconciling bank statements or preparing monthly expense breakdowns.

Where it's implemented
- Backend: `Backend/main.py` endpoints:
  - POST `/api/expenses` — add an expense
  - GET `/api/expenses` — list all expenses
  - GET `/api/expenses/category/{cat_name}` — category scoped list + totals
  - PUT `/api/expenses/{expense_id}` and DELETE `/api/expenses/{expense_id}` — modify/remove
- Frontend: UI pages/components in `Frontend/app` and `Frontend/components` call these endpoints and render forms, lists and charts.

Why this approach
- Server-side ledgering (raw SQL) gives a single source of truth, atomic writes, and the ability to index by user/date/category for fast queries and reliable auditing.
- Centralizing validation and permission checks on the backend prevents data inconsistencies between clients.

---

### Budget Management
- **Set Monthly Budgets**: Define spending limits for each month
- **Budget vs Actual**: Real-time comparison of actual spending vs budgeted amount
- **Smart Alerts**: Get notifications when you're:
  - Under budget (with remaining balance)
  - Over budget (with overspend amount)
  - Exactly on budget
- **View All Budgets**: See all your monthly budget allocations

When to use
- Set or update monthly budgets at the start of a month or when planning finances.
- Use budget checks mid-month to decide spending adjustments.

Where it's implemented
- Backend: `Backend/main.py` endpoints:
  - POST `/api/budgets` — set/update budget
  - GET `/api/budgets` — list budgets
  - GET `/api/budgets/check/{month_name}` — returns budget_limit, actual_expense, remaining_balance, status
- Database: `Database/truebalance_db.sql` contains views like `monthly_summary` for analytics (may need conversion to Postgres).
- Frontend: Budget UI in `Frontend/app` uses these endpoints to display monthly summaries and trigger alerts.

Why this approach
- Storing budgets server-side ensures consistency across devices and lets the backend compute aggregates and alerts efficiently.
- Using DB views or server-side aggregation reduces frontend work and provides performant dashboard queries.

---

### Financial Calculators
- **Simple Interest Calculator**n- **Compound Interest Calculator**
- **Loan Amortization**
- **Income Tax Calculator (Indian slabs)**
- **SIP Calculator**

When to use
- For planning or "what-if" analysis: estimate returns, monthly EMI, or tax due before making financial decisions.

Where it's implemented
- Backend: Stateless endpoints in `Backend/main.py` under `/api/calculator/*`. They accept form inputs and return computed JSON without DB writes (examples: `/api/calculator/compound-interest`, `/api/calculator/loan-amortization`).
- Frontend: Calculator UI in `Frontend/app` calls the endpoints and shows results.

Why this approach
- Centralizing numerical logic on the server enforces a single authoritative implementation, simplifies testing, and makes it easy to change formulas in one place.
- Stateless endpoints require no DB writes and are cheap to run and cache if needed.

## Tech Stack

- **Frontend**: TypeScript, Next.js, React 19, TailwindCSS, Radix UI
- **Backend**: Python, FastAPI
- **Database**: MySQL (schema provided) — backend supports PostgreSQL (via DATABASE_URL) and has a local SQLite fallback
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

## Deployment (short)

Recommended quick setup: host the Next.js frontend on Vercel (or any static/SSR host) and the FastAPI backend as a small service (Render, Cloud Run, or a Docker host). Use a managed Postgres (Neon, Heroku Postgres, etc.) and set DATABASE_URL for the backend. Keep deployment details minimal here — use the README steps under "Getting Started" to run locally and refer to your chosen provider's docs for production deployment.

Note: Database/truebalance_db.sql is MySQL‑flavored while the backend code uses psycopg2 (Postgres). Pick a production DB (Postgres recommended) and convert the schema or adapt the backend accordingly; the backend has a SQLite fallback for local dev.

## One-command developer helpers (optional)

Use root `Makefile` commands:

```bash
make setup          # Installs backend + frontend dependencies
make setup-env      # Copies .env.example to Backend/.env (if missing)
make db-bootstrap   # Imports Database/truebalance_db.sql into your DATABASE
make dev-backend    # Runs backend
make dev-frontend    # Runs frontend
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
