# TrueBalance: Financial Analytics & Management Engine

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![MySQL](https://img.shields.io/badge/mysql-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) ![NestJS](https://img.shields.io/badge/nestjs-%23E0234E.svg?style=for-the-badge&logo=nestjs&logoColor=white) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB) ![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white) ![Radix UI](https://img.shields.io/badge/radix%20ui-161618.svg?style=for-the-badge&logo=radix-ui&logoColor=white)

TrueBalance is a full-stack personal finance application engineered to bridge the gap between daily expense tracking and long-term wealth forecasting. It combines a secure relational ledger with a suite of deterministic mathematical planning engines.

- 100% Transaction Ledgering: Safely records every inflow and outflow with zero data loss, using optimized database indexing for instant categorical filtering (Food, Utilities, Education).

- Proactive Budget Guard: Continuously computes aggregate monthly spending against customizable limits, delivering real-time variance metrics to actively prevent overruns.

- Precision Forecasting Matrix: Packed with 50+ integrated calculations providing mathematically exact projections for SIPs, compounding assets, progressive tax slabs, and amortized loan schedules.

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

```
True_Balance/
├── Frontend/          # Next.js React application
├── Backend/           # FastAPI Python backend
└── Database/          # MySQL database schemas
```

## Getting Started

### Prerequisites
- Node.js 18+ (for Frontend)
- Python 3.8+ (for Backend)
- MySQL 8.0+ (for Database)

### Backend Setup

1. **Install Dependencies**
   ```bash
   cd Backend
   pip install fastapi mysql-connector-python python-multipart
   ```

2. **Configure Database**
   - Update `DB_CONFIG` in `Backend/main.py` with your MySQL credentials
   - Ensure MySQL is running

3. **Run Backend**
   ```bash
   cd Backend
   python main.py
   ```
   Backend runs on `http://localhost:8000`

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd Frontend
   npm install
   ```

2. **Run Development Server**
   ```bash
   npm run dev
   ```
   Frontend runs on `http://localhost:3000`

3. **Build for Production**
   ```bash
   npm run build
   npm start
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

## Database Schema

### Expenses Table
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `date` (DATE)
- `month` (VARCHAR)
- `category` (VARCHAR)
- `amount` (DECIMAL)
- `created_at` (TIMESTAMP)

### Budgets Table
- `id` (INT, AUTO_INCREMENT, PRIMARY KEY)
- `month` (VARCHAR, UNIQUE)
- `budget` (DECIMAL)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

---

**Made by Hesenberg-25**
