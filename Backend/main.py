from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
import mysql.connector
from mysql.connector import Error
import math
import time
from contextlib import contextmanager
import os
from dotenv import load_dotenv

app = FastAPI(title="TrueBalance API Backend")

# Enable CORS so your frontend tool can securely connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    "host": os.environ.get("HOST"),
    "user": os.environ.get("USER"),
    "password": os.environ.get("PASSWORD"),
    "database": os.environ.get("DATABASE")
}

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        yield connection
    except Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if connection and connection.is_connected():
            connection.close()

def init_database():
    """Initialize database tables"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create Expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    month VARCHAR(10) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create Budget table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    month VARCHAR(10) NOT NULL UNIQUE,
                    budget DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("Database tables initialized successfully!")
    except Error as e:
        print(f"Error initializing database: {e}")

# Initialize database on startup
init_database()

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK (MUST BE FIRST)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "TrueBalance API is running"}

# ═══════════════════════════════════════════════════════════════
# 1. EXPENSE TRACKER MODULE (MySQL Version)
# ═══════════════════════════════════════════════════════════════

def get_monthly_expense_logic(month_name: str) -> float:
    """Get total expenses for a specific month from MySQL"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT SUM(amount) as total FROM expenses WHERE month = %s",
                (month_name,)
            )
            result = cursor.fetchone()
            return float(result['total']) if result['total'] else 0.0
    except Error as e:
        print(f"Error fetching monthly expenses: {e}")
        return 0.0

@app.post("/api/expenses")
async def add_expense_endpoint(category_name: str = Form(...), amount: float = Form(...)):
    """Add expense to MySQL database"""
    if category_name not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {CATEGORIES}")
    
    date_today = date.today()
    month_today = date_today.month
    month_string = MONTHS[month_today - 1].capitalize()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO expenses (date, month, category, amount) VALUES (%s, %s, %s, %s)",
                (date_today, month_string, category_name, amount)
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
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error adding expense: {str(e)}")

@app.get("/api/expenses")
async def get_all_expenses():
    """Retrieve all expenses from MySQL"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, date, month, category, amount FROM expenses ORDER BY date DESC")
            expenses = cursor.fetchall()
            
            # Convert date objects to strings for JSON serialization
            for expense in expenses:
                expense['date'] = str(expense['date'])
                expense['amount'] = float(expense['amount'])
            
            return expenses
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")

@app.get("/api/expenses/category/{cat_name}")
async def see_desired_expense_endpoint(cat_name: str):
    """Get expenses for a specific category from MySQL"""
    if cat_name not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Category not found")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, date, month, category, amount FROM expenses WHERE category = %s ORDER BY date DESC",
                (cat_name,)
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
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category expenses: {str(e)}")

@app.delete("/api/expenses/{expense_id}")
async def delete_expense_endpoint(expense_id: int):
    """Delete an expense from MySQL"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Expense not found")
            
            return {
                "status": "success",
                "message": f"Expense with ID {expense_id} deleted successfully"
            }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error deleting expense: {str(e)}")

@app.put("/api/expenses/{expense_id}")
async def update_expense_endpoint(expense_id: int, category_name: str = Form(...), amount: float = Form(...)):
    """Update an expense in MySQL"""
    if category_name not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of {CATEGORIES}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE expenses SET category = %s, amount = %s WHERE id = %s",
                (category_name, amount, expense_id)
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
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error updating expense: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# 2. BUDGET TRACKER MODULE (MySQL Version)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/budgets")
async def set_budget_endpoint(month_idx: int = Form(...), budget: float = Form(...)):
    """Set or update budget in MySQL"""
    if month_idx < 1 or month_idx > 12:
        raise HTTPException(status_code=400, detail="Month index must be between 1 and 12")
    
    month_name = MONTHS[month_idx - 1]
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if budget already exists
            cursor.execute("SELECT id FROM budgets WHERE month = %s", (month_name,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute(
                    "UPDATE budgets SET budget = %s WHERE month = %s",
                    (budget, month_name)
                )
                message = f"Budget for {month_name} updated successfully!"
            else:
                cursor.execute(
                    "INSERT INTO budgets (month, budget) VALUES (%s, %s)",
                    (month_name, budget)
                )
                message = f"Budget for {month_name} added successfully!"
            
            conn.commit()
            
            return {
                "status": "success",
                "message": message
            }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error setting budget: {str(e)}")

@app.get("/api/budgets")
async def get_all_budgets():
    """Get all budgets from MySQL"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT month, budget FROM budgets ORDER BY month")
            budgets = cursor.fetchall()
            
            for budget in budgets:
                budget['budget'] = float(budget['budget'])
            
            return budgets
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error fetching budgets: {str(e)}")

@app.get("/api/budgets/check/{month_name}")
async def check_budget_endpoint(month_name: str):
    """Check budget vs actual expenses from MySQL"""
    if month_name not in MONTHS:
        raise HTTPException(status_code=400, detail="Invalid month name acronym")
    
    try:
        # Get actual expenses
        actual_expense = get_monthly_expense_logic(month_name)
        
        # Get budget
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT budget FROM budgets WHERE month = %s", (month_name,))
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
    except Error as e:
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