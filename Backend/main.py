from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
import math
import time
from contextlib import contextmanager

import os
import sqlite3
import base64
import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path
from dotenv import load_dotenv
app = FastAPI(title="TrueBalance API Backend")

AUTH_COOKIE = "truebalance_session"
SESSION_SECRET = os.environ.get("SESSION_SECRET", "change-this-session-secret")
SESSION_MAX_AGE = 60 * 60 * 24 * 30

# Enable CORS so your frontend tool can securely connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "FRONTEND_URL", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CATEGORIES = ["Food", "Transport", "Household", "Education", "Health", "Utilities", "Other"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ═══════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════


load_dotenv()

DB_CONFIG = {
    "host": os.environ.get("PGHOST"),
    "port": os.environ.get("PGPORT", "5432"),
    "user": os.environ.get("PGUSER"),
    "password": os.environ.get("PGPASSWORD"),
    "dbname": os.environ.get("PGDATABASE"),
}

DB_ERRORS = (Error, sqlite3.Error)
USE_SQLITE = not (
    os.environ.get("DATABASE_URL")
    or any(os.environ.get(name) for name in ("PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE"))
)


class SQLiteCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, parameters=()):
        return self._cursor.execute(query.replace("%s", "?"), parameters)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class SQLiteConnection:
    def __init__(self, database_path):
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = lambda cursor, row: {
            column[0]: row[index] for index, column in enumerate(cursor.description)
        }

    def cursor(self, cursor_factory=None):
        return SQLiteCursor(self._connection.cursor())

    def __getattr__(self, name):
        return getattr(self._connection, name)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        database_url = os.environ.get("DATABASE_URL")
        if USE_SQLITE:
            database_path = os.environ.get(
                "SQLITE_DATABASE",
                str(Path(__file__).resolve().parent.parent / "truebalance.db"),
            )
            connection = SQLiteConnection(database_path)
        else:
            connection = psycopg2.connect(database_url) if database_url else psycopg2.connect(**DB_CONFIG)
        yield connection
    except DB_ERRORS as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if connection:
            connection.close()

def init_database():
    """Initialize database tables"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            expense_id_definition = "INTEGER PRIMARY KEY AUTOINCREMENT" if USE_SQLITE else "SERIAL PRIMARY KEY"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS expenses (
                    id {expense_id_definition},
                    user_id INTEGER,
                    date DATE NOT NULL,
                    month VARCHAR(10) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            budget_id_definition = "INTEGER PRIMARY KEY AUTOINCREMENT" if USE_SQLITE else "SERIAL PRIMARY KEY"
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS budgets (
                    id {budget_id_definition},
                    user_id INTEGER,
                    month VARCHAR(10) NOT NULL,
                    budget DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, month)
                )
            """)

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS users (
                    id {"INTEGER PRIMARY KEY AUTOINCREMENT" if USE_SQLITE else "SERIAL PRIMARY KEY"},
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            for table in ("expenses", "budgets"):
                try:
                    cursor.execute("SAVEPOINT add_user_id_column")
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
                    cursor.execute("RELEASE SAVEPOINT add_user_id_column")
                except DB_ERRORS:
                    cursor.execute("ROLLBACK TO SAVEPOINT add_user_id_column")
                    cursor.execute("RELEASE SAVEPOINT add_user_id_column")
            if not USE_SQLITE:
                cursor.execute("SAVEPOINT drop_budget_constraint")
                try:
                    cursor.execute("ALTER TABLE budgets DROP CONSTRAINT IF EXISTS budgets_month_key")
                    cursor.execute("RELEASE SAVEPOINT drop_budget_constraint")
                except DB_ERRORS:
                    cursor.execute("ROLLBACK TO SAVEPOINT drop_budget_constraint")
                    cursor.execute("RELEASE SAVEPOINT drop_budget_constraint")
            
            conn.commit()
            print("Database tables initialized successfully!")
    except DB_ERRORS as e:
        print(f"Error initializing database: {e}")

# Initialize database on startup
init_database()


def _encode_session(user_id: int, remember: bool) -> str:
    payload = {"user_id": user_id, "exp": int(time.time()) + (SESSION_MAX_AGE if remember else 60 * 60 * 8)}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(SESSION_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def _decode_session(token: str | None) -> int | None:
    if not token or "." not in token:
        return None
    body, signature = token.rsplit(".", 1)
    expected = hmac.new(SESSION_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode((body + "=" * (-len(body) % 4)).encode()))
        if payload["exp"] < time.time():
            return None
        return int(payload["user_id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256$310000${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.urlsafe_b64decode(salt), int(rounds))
        return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), expected)
    except (ValueError, TypeError):
        return False


def get_current_user(truebalance_session: str | None = Cookie(default=None)) -> dict:
    user_id = _decode_session(truebalance_session)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def set_session_cookie(response: Response, user_id: int, remember: bool) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        _encode_session(user_id, remember),
        max_age=SESSION_MAX_AGE if remember else 60 * 60 * 8,
        httponly=True,
        secure=not USE_SQLITE,
        samesite="lax",
    )


@app.post("/api/auth/signup")
async def signup(response: Response, email: str = Form(...), password: str = Form(...), remember: bool = Form(False)):
    email = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_SQLITE:
                cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, _hash_password(password)))
                user_id = cursor.lastrowid
            else:
                cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id", (email, _hash_password(password)))
                user_id = cursor.fetchone()[0]
            conn.commit()
    except DB_ERRORS as error:
        if "unique" in str(error).lower() or "duplicate" in str(error).lower():
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        raise HTTPException(status_code=500, detail="Unable to create account")
    set_session_cookie(response, int(user_id), remember)
    return {"email": email}


@app.post("/api/auth/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...), remember: bool = Form(False)):
    email = email.strip().lower()
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    set_session_cookie(response, int(user["id"]), remember)
    return {"email": user["email"]}


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE)
    return {"status": "success"}


@app.get("/api/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return {"email": user["email"]}

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK (MUST BE FIRST)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "TrueBalance API is running"}

# ═══════════════════════════════════════════════════════════════
# 1. EXPENSE TRACKER MODULE
# ═══════════════════════════════════════════════════════════════

def get_monthly_expense_logic(month_name: str, user_id: int) -> float:
    """Get total expenses for a specific month"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT SUM(amount) as total FROM expenses WHERE month = %s AND user_id = %s",
                (month_name, user_id)
            )
            result = cursor.fetchone()
            return float(result['total']) if result['total'] else 0.0
    except DB_ERRORS as e:
        print(f"Error fetching monthly expenses: {e}")
        return 0.0

@app.post("/api/expenses")
async def add_expense_endpoint(category_name: str = Form(...), amount: float = Form(...), user: dict = Depends(get_current_user)):
    """Add expense to the database"""
    if category_name not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {CATEGORIES}")
    
    date_today = date.today()
    month_today = date_today.month
    month_string = MONTHS[month_today - 1].capitalize()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (user_id, date, month, category, amount) VALUES (%s, %s, %s, %s, %s)",
                (user["id"], date_today, month_string, category_name, amount)
            )
            conn.commit()
            
            return {
                "status": "success", 
                "message": f"Expense Spent on {category_name} : {amount}",
                "data": {
                    "date": str(date_today), 
                    "month": month_string, 
                    "category": category_name, 
                    "amount": amount
                }
            }
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error adding expense: {str(e)}")

@app.get("/api/expenses")
async def get_all_expenses(user: dict = Depends(get_current_user)):
    """Retrieve all expenses"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT id, date, month, category, amount FROM expenses WHERE user_id = %s ORDER BY date DESC", (user["id"],))
            expenses = cursor.fetchall()
            
            # Convert date objects to strings for JSON serialization
            for expense in expenses:
                expense['date'] = str(expense['date'])
                expense['amount'] = float(expense['amount'])
            
            return expenses
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")

@app.get("/api/expenses/category/{cat_name}")
async def see_desired_expense_endpoint(cat_name: str, user: dict = Depends(get_current_user)):
    """Get expenses for a specific category"""
    if cat_name not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Category not found")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT id, date, month, category, amount FROM expenses WHERE category = %s AND user_id = %s ORDER BY date DESC",
                (cat_name, user["id"])
            )
            records = cursor.fetchall()
            
            # Convert data types for JSON
            for record in records:
                record['date'] = str(record['date'])
                record['amount'] = float(record['amount'])
            
            # Calculate total
            total_category = sum(record['amount'] for record in records)
            
            return {
                "category": cat_name, 
                "total_spent": total_category, 
                "records": records
            }
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category expenses: {str(e)}")

@app.delete("/api/expenses/{expense_id}")
async def delete_expense_endpoint(expense_id: int, user: dict = Depends(get_current_user)):
    """Delete an expense"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (expense_id, user["id"]))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Expense not found")
            
            return {
                "status": "success",
                "message": f"Expense with ID {expense_id} deleted successfully"
            }
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error deleting expense: {str(e)}")

@app.put("/api/expenses/{expense_id}")
async def update_expense_endpoint(expense_id: int, category_name: str = Form(...), amount: float = Form(...), user: dict = Depends(get_current_user)):
    """Update an expense"""
    if category_name not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {CATEGORIES}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE expenses SET category = %s, amount = %s WHERE id = %s AND user_id = %s",
                (category_name, amount, expense_id, user["id"])
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Expense not found")
            
            return {
                "status": "success",
                "message": f"Expense updated successfully",
                "data": {
                    "id": expense_id,
                    "category": category_name,
                    "amount": amount
                }
            }
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error updating expense: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# 2. BUDGET TRACKER MODULE
# ═══════════════════════════════════════════════════════════════

@app.post("/api/budgets")
async def set_budget_endpoint(month_idx: int = Form(...), budget: float = Form(...), user: dict = Depends(get_current_user)):
    """Set or update a budget"""
    if month_idx < 1 or month_idx > 12:
        raise HTTPException(status_code=400, detail="Month index must be between 1 and 12")
    
    month_name = MONTHS[month_idx - 1]
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if budget already exists
            cursor.execute("SELECT id FROM budgets WHERE month = %s AND user_id = %s", (month_name, user["id"]))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE budgets SET budget = %s WHERE month = %s AND user_id = %s",
                    (budget, month_name, user["id"])
                )
                message = f"Budget for {month_name} updated successfully!"
            else:
                cursor.execute(
                    "INSERT INTO budgets (user_id, month, budget) VALUES (%s, %s, %s)",
                    (user["id"], month_name, budget)
                )
                message = f"Budget for {month_name} added successfully!"
            
            conn.commit()
            
            return {
                "status": "success",
                "message": message
            }
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error setting budget: {str(e)}")

@app.get("/api/budgets")
async def get_all_budgets(user: dict = Depends(get_current_user)):
    """Get all budgets"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT month, budget FROM budgets WHERE user_id = %s ORDER BY month", (user["id"],))
            budgets = cursor.fetchall()
            
            for budget in budgets:
                budget['budget'] = float(budget['budget'])
            
            return budgets
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error fetching budgets: {str(e)}")

@app.get("/api/budgets/check/{month_name}")
async def check_budget_endpoint(month_name: str, user: dict = Depends(get_current_user)):
    """Check budget vs actual expenses"""
    if month_name not in MONTHS:
        raise HTTPException(status_code=400, detail="Invalid month name acronym")
    
    try:
        # Get actual expenses
        actual_expense = get_monthly_expense_logic(month_name, user["id"])
        
        # Get budget
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT budget FROM budgets WHERE month = %s AND user_id = %s", (month_name, user["id"]))
            result = cursor.fetchone()
            setted_budget = float(result['budget']) if result else 0.0
        
        remaining = setted_budget - actual_expense
        
        if actual_expense < setted_budget:
            status = "under"
            msg = f"Hushhh!! You still have {remaining} to spend. Use them wisely."
        elif actual_expense > setted_budget:
            status = "over"
            msg = f"Warning!! You have exceeded your budget by {abs(remaining)}."
        else:
            status = "exact"
            msg = "You are exactly on budget! Be careful."
        
        return {
            "month": month_name,
            "budget_limit": setted_budget,
            "actual_expense": actual_expense,
            "remaining_balance": remaining,
            "status_code": status,
            "message": msg
        }
    except DB_ERRORS as e:
        raise HTTPException(status_code=500, detail=f"Error checking budget: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# 3. INTEREST CALCULATOR MODULE (Pure Math Conversions - No DB needed)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/calculator/simple-interest")
async def simple_interest_api(principal: float = Form(...), rate: float = Form(...), years: float = Form(...)):
    interest = (principal * rate * years) / 100
    return {"interest_earned": interest, "total_maturity_amount": principal + interest}

@app.post("/api/calculator/compound-interest")
async def compound_interest_api(principal: float = Form(...), rate: float = Form(...), years: float = Form(...), frequency: int = Form(...)):
    rate_fraction = rate / 100
    total_return = principal * pow((1 + (rate_fraction / frequency)), (frequency * years))
    return {"interest_earned": total_return - principal, "total_maturity_amount": total_return}

@app.post("/api/calculator/loan-amortization")
async def loan_amortization_api(principal: float = Form(...), rate: float = Form(...), months_len: int = Form(...)):
    monthly_rate = rate / (12 * 100)
    emi = (principal * monthly_rate * pow(1 + monthly_rate, months_len)) / (pow(1 + monthly_rate, months_len) - 1)
    
    schedule = []
    remaining_p = principal
    total_int = 0
    
    for i in range(1, months_len + 1):
        interest_d = remaining_p * monthly_rate
        principal_d = emi - interest_d
        remaining_p -= principal_d
        total_int += interest_d
        schedule.append({
            "month": i,
            "emi": round(emi, 2),
            "principal_paid": round(principal_d, 2),
            "interest_paid": round(interest_d, 2),
            "remaining_principal": round(max(0, remaining_p), 2)
        })
    
    return {
        "monthly_emi": round(emi, 2),
        "total_amount_payable": round(emi * months_len, 2),
        "total_interest_payable": round(total_int, 2),
        "schedule": schedule
    }

@app.post("/api/calculator/taxation")
async def taxation_api(income: float = Form(...)):
    tax = 0
    slabs = []
    if income <= 400000:
        tax = 0
        slabs.append({"slab": "Up to 4L", "tax": 0})
    elif income <= 800000:
        tax = (income - 400000) * 0.05
        slabs.append({"slab": "4L - 8L (5%)", "tax": tax})
    elif income <= 1200000:
        tax = (400000 * 0.05) + (income - 800000) * 0.10
        slabs.append({"slab": "4L - 8L (5%)", "tax": 400000 * 0.05})
        slabs.append({"slab": "8L - 12L (10%)", "tax": (income - 800000) * 0.10})
    elif income <= 1600000:
        tax = (400000 * 0.05) + (400000 * 0.10) + (income - 1200000) * 0.15
        slabs.append({"slab": "4L - 8L (5%)", "tax": 400000 * 0.05})
        slabs.append({"slab": "8L - 12L (10%)", "tax": 400000 * 0.10})
        slabs.append({"slab": "12L - 16L (15%)", "tax": (income - 1200000) * 0.15})
    elif income <= 2000000:
        tax = (400000 * 0.05) + (400000 * 0.10) + (400000 * 0.15) + (income - 1600000) * 0.20
        slabs.append({"slab": "4L - 8L (5%)", "tax": 400000 * 0.05})
        slabs.append({"slab": "8L - 12L (10%)", "tax": 400000 * 0.10})
        slabs.append({"slab": "8L - 12L (10%)", "tax": 400000 * 0.15})
        slabs.append({"slab": "16L - 20L (20%)", "tax": (income - 1600000) * 0.20})
    else:
        tax = (400000 * 0.05) + (400000 * 0.10) + (400000 * 0.15) + (400000 * 0.20) + (income - 2000000) * 0.30
        slabs.append({"slab": "4L - 8L (5%)", "tax": 400000 * 0.05})
        slabs.append({"slab": "8L - 12L (10%)", "tax": 400000 * 0.10})
        slabs.append({"slab": "12L - 16L (15%)", "tax": 400000 * 0.15})
        slabs.append({"slab": "16L - 20L (20%)", "tax": 400000 * 0.20})
        slabs.append({"slab": "Above 20L (30%)", "tax": (income - 2000000) * 0.30})
    
    surcharge = 0
    if income > 5000000:
        surcharge = tax * 0.10
    
    cess = (tax + surcharge) * 0.04
    total_tax = tax + surcharge + cess
    
    return {
        "base_tax": round(tax, 2),
        "surcharge": round(surcharge, 2),
        "cess_health_education": round(cess, 2),
        "total_tax_payable": round(total_tax, 2),
        "breakdown_slabs": slabs
    }

@app.post("/api/calculator/sip")
async def sip_api(principal_monthly: float = Form(...), annual_rate: float = Form(...), years: float = Form(...)):
    compound_frequency = annual_rate / (100 * 12)
    time_frequency = years * 12
    
    growth_factor = (pow((1 + compound_frequency), time_frequency) - 1) / compound_frequency
    maturity_amount = (principal_monthly) * (growth_factor) * (1 + compound_frequency)
    invested_amount = principal_monthly * time_frequency
    profit_gained = maturity_amount - invested_amount
    
    return {
        "total_invested": round(invested_amount, 2),
        "maturity_value": round(maturity_amount, 2),
        "wealth_gained": round(profit_gained, 2)
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))