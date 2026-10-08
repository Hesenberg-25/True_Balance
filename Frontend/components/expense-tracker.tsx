"use client";

import { useState, useEffect, useMemo } from "react";
import { Plus, Filter, Receipt, X, Trash2, AlertTriangle, CalendarDays, Calculator, Pencil } from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  addExpense,
  updateExpense,
  deleteExpense,
  getAllExpenses,
  CATEGORIES,
  type Expense,
  type Category,
} from "@/lib/api";

const COLORS = [
  "oklch(0.55 0.18 155)",
  "oklch(0.60 0.12 200)",
  "oklch(0.65 0.15 280)",
  "oklch(0.70 0.12 45)",
  "oklch(0.55 0.15 330)",
  "oklch(0.60 0.10 100)",
  "oklch(0.50 0.12 240)",
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 24,
    },
  },
};

const modalVariants = {
  hidden: { opacity: 0, scale: 0.9, y: 20 },
  visible: { 
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 25,
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.9, 
    y: 20,
    transition: { duration: 0.2 }
  },
};

function getToday() {
  const today = new Date();
  const offset = today.getTimezoneOffset() * 60000;
  return new Date(today.getTime() - offset).toISOString().slice(0, 10);
}

function parseExpenseDate(value: string) {
  return new Date(`${value}T00:00:00`);
}

function formatExpenseDate(value: string) {
  return parseExpenseDate(value).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

type CalculatorOperator = "+" | "−" | "×" | "÷" | null;

export function ExpenseTracker() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Expense | null>(null);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [filterCategory, setFilterCategory] = useState<string>("All");
  const [showCalculator, setShowCalculator] = useState(false);
  const [calculatorDisplay, setCalculatorDisplay] = useState("0");
  const [calculatorValue, setCalculatorValue] = useState<number | null>(null);
  const [calculatorOperator, setCalculatorOperator] = useState<CalculatorOperator>(null);
  const [calculatorWaiting, setCalculatorWaiting] = useState(false);
  
  const [formData, setFormData] = useState({
    category: "Food" as Category,
    amount: "",
    date: getToday(),
    notes: "",
  });

  function resetCalculator() {
    setCalculatorDisplay("0");
    setCalculatorValue(null);
    setCalculatorOperator(null);
    setCalculatorWaiting(false);
  }

  function enterCalculatorDigit(digit: string) {
    if (calculatorWaiting || calculatorDisplay === "0") {
      setCalculatorDisplay(digit);
      setCalculatorWaiting(false);
      return;
    }
    setCalculatorDisplay(`${calculatorDisplay}${digit}`);
  }

  function enterCalculatorDecimal() {
    if (calculatorWaiting) {
      setCalculatorDisplay("0.");
      setCalculatorWaiting(false);
    } else if (!calculatorDisplay.includes(".")) {
      setCalculatorDisplay(`${calculatorDisplay}.`);
    }
  }

  function calculateResult(firstValue: number, secondValue: number, operator: CalculatorOperator) {
    if (operator === "+") return firstValue + secondValue;
    if (operator === "−") return firstValue - secondValue;
    if (operator === "×") return firstValue * secondValue;
    if (operator === "÷") return secondValue === 0 ? null : firstValue / secondValue;
    return secondValue;
  }

  function chooseCalculatorOperator(operator: CalculatorOperator) {
    const currentValue = Number(calculatorDisplay);
    if (!Number.isFinite(currentValue)) return;

    if (calculatorValue !== null && calculatorOperator && !calculatorWaiting) {
      const result = calculateResult(calculatorValue, currentValue, calculatorOperator);
      if (result === null) {
        resetCalculator();
        return;
      }
      setCalculatorValue(result);
      setCalculatorDisplay(String(result));
    } else {
      setCalculatorValue(currentValue);
    }
    setCalculatorOperator(operator);
    setCalculatorWaiting(true);
  }

  function completeCalculator() {
    if (calculatorValue === null || !calculatorOperator) {
      setFormData((currentFormData) => ({ ...currentFormData, amount: calculatorDisplay }));
      return;
    }

    const result = calculateResult(calculatorValue, Number(calculatorDisplay), calculatorOperator);
    if (result === null || !Number.isFinite(result)) {
      resetCalculator();
      return;
    }
    const formattedResult = String(Number(result.toFixed(2)));
    setCalculatorDisplay(formattedResult);
    setFormData((currentFormData) => ({ ...currentFormData, amount: formattedResult }));
    setShowCalculator(false);
    setCalculatorValue(null);
    setCalculatorOperator(null);
    setCalculatorWaiting(true);
  }

  useEffect(() => {
    fetchExpenses();
  }, []);

  async function fetchExpenses() {
    try {
      const data = await getAllExpenses();
      setExpenses(data);
    } catch {
      setExpenses([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.amount || parseFloat(formData.amount) <= 0) return;

    setSubmitting(true);
    try {
      if (editingExpense) {
        await updateExpense(editingExpense.Id, formData.category, parseFloat(formData.amount), formData.date, formData.notes);
      } else {
        await addExpense(formData.category, parseFloat(formData.amount), formData.date, formData.notes);
      }
      setFormData({ category: "Food", amount: "", date: getToday(), notes: "" });
      setEditingExpense(null);
      setShowCalculator(false);
      resetCalculator();
      setShowForm(false);
      await fetchExpenses();
    } catch (error) {
      console.error(editingExpense ? "Failed to update expense:" : "Failed to add expense:", error);
    } finally {
      setSubmitting(false);
    }
  }

  function startEditing(expense: Expense) {
    setEditingExpense(expense);
    setFormData({
      category: expense.Category as Category,
      amount: String(expense.Amount),
      date: expense.Date,
      notes: expense.Notes,
    });
    setShowForm(true);
  }

  async function confirmDelete() {
    if (!pendingDelete) return;

    const expense = pendingDelete;
    setPendingDelete(null);
    setDeletingId(expense.Id);
    try {
      await deleteExpense(expense.Id);
      setExpenses((currentExpenses) =>
        currentExpenses.filter((currentExpense) => currentExpense.Id !== expense.Id),
      );
    } catch (error) {
      console.error("Failed to delete expense:", error);
    } finally {
      setDeletingId(null);
    }
  }

  const filteredExpenses = useMemo(() => {
    if (filterCategory === "All") return expenses;
    return expenses.filter((e) => e.Category === filterCategory);
  }, [expenses, filterCategory]);

  const categoryData = useMemo(() => {
    const byCategory = filteredExpenses.reduce((acc, e) => {
      acc[e.Category] = (acc[e.Category] || 0) + e.Amount;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(byCategory).map(([name, value]) => ({
      name,
      value,
    }));
  }, [filteredExpenses]);

  const totalFiltered = filteredExpenses.reduce((sum, e) => sum + e.Amount, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div 
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
          className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <motion.div 
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Header */}
      <motion.div 
        variants={itemVariants}
        className="flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold">Expense Tracker</h1>
          <p className="text-muted-foreground mt-1">
            Track and categorize your spending
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            setEditingExpense(null);
            setFormData({ category: "Food", amount: "", date: getToday(), notes: "" });
            setShowForm(true);
          }}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Expense
        </motion.button>
      </motion.div>

      {/* Add Expense Modal */}
      <AnimatePresence>
        {showForm && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowForm(false)}
          >
            <motion.div 
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(e) => e.stopPropagation()}
              className="bg-card rounded-xl border border-border shadow-lg w-full max-w-md p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">{editingExpense ? "Edit Expense" : "Add New Expense"}</h2>
                <motion.button
                  whileHover={{ scale: 1.1, rotate: 90 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => {
                    setShowForm(false);
                    setEditingExpense(null);
                  }}
                  className="p-1 hover:bg-muted rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </motion.button>
              </div>
              <form onSubmit={handleSubmit} className="space-y-4">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <label className="block text-sm font-medium mb-2">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) =>
                      setFormData({ ...formData, category: e.target.value as Category })
                    }
                    className="w-full px-4 py-2.5 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium" htmlFor="expense-amount">Amount (₹)</label>
                    <button
                      type="button"
                      onClick={() => setShowCalculator((isVisible) => !isVisible)}
                      aria-label={showCalculator ? "Hide calculator" : "Show calculator"}
                      title={showCalculator ? "Hide calculator" : "Show calculator"}
                      className={`inline-flex items-center justify-center rounded-md p-1.5 transition-colors ${showCalculator ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}
                    >
                      <Calculator className="w-4 h-4" />
                    </button>
                  </div>
                  <input
                    id="expense-amount"
                    type="number"
                    min="0"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) =>
                      setFormData({ ...formData, amount: e.target.value })
                    }
                    placeholder="Enter amount"
                    className="w-full px-4 py-2.5 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                  />
                  {showCalculator && <div
                    className="fixed inset-0 z-60 flex items-center justify-center bg-foreground/25 backdrop-blur-sm p-4"
                    onClick={() => setShowCalculator(false)}
                  >
                    <div
                      className="bg-card rounded-xl border border-border shadow-xl w-full max-w-xs p-4"
                      onClick={(event) => event.stopPropagation()}
                    >
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2 text-sm font-semibold">
                          <Calculator className="w-4 h-4 text-primary" />
                          Calculator
                        </div>
                        <button
                          type="button"
                          onClick={() => setShowCalculator(false)}
                          aria-label="Close calculator"
                          className="p-1 text-muted-foreground hover:bg-muted rounded-md transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="rounded-lg bg-muted/50 border border-border px-3 py-2 mb-3 text-right">
                        <span className="font-mono text-xl font-semibold text-foreground truncate block" aria-live="polite">
                          {calculatorDisplay}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-1.5">
                      {["7", "8", "9"].map((digit) => (
                        <button key={digit} type="button" onClick={() => enterCalculatorDigit(digit)} className="h-8 rounded-md bg-card border border-border text-sm font-medium hover:bg-muted transition-colors">{digit}</button>
                      ))}
                      <button type="button" onClick={() => chooseCalculatorOperator("÷")} className="h-8 rounded-md bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors">÷</button>
                      {["4", "5", "6"].map((digit) => (
                        <button key={digit} type="button" onClick={() => enterCalculatorDigit(digit)} className="h-8 rounded-md bg-card border border-border text-sm font-medium hover:bg-muted transition-colors">{digit}</button>
                      ))}
                      <button type="button" onClick={() => chooseCalculatorOperator("×")} className="h-8 rounded-md bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors">×</button>
                      {["1", "2", "3"].map((digit) => (
                        <button key={digit} type="button" onClick={() => enterCalculatorDigit(digit)} className="h-8 rounded-md bg-card border border-border text-sm font-medium hover:bg-muted transition-colors">{digit}</button>
                      ))}
                      <button type="button" onClick={() => chooseCalculatorOperator("−")} className="h-8 rounded-md bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors">−</button>
                      <button type="button" onClick={() => enterCalculatorDigit("0")} className="h-8 rounded-md bg-card border border-border text-sm font-medium hover:bg-muted transition-colors">0</button>
                      <button type="button" onClick={enterCalculatorDecimal} className="h-8 rounded-md bg-card border border-border text-sm font-medium hover:bg-muted transition-colors">.</button>
                      <button type="button" onClick={resetCalculator} className="h-8 rounded-md bg-muted text-xs font-semibold hover:bg-muted/80 transition-colors">Clear</button>
                      <button type="button" onClick={() => chooseCalculatorOperator("+")} className="h-8 rounded-md bg-primary/10 text-primary text-sm font-semibold hover:bg-primary/20 transition-colors">+</button>
                      <button type="button" onClick={completeCalculator} className="col-span-4 h-8 rounded-md bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors">Use result</button>
                      </div>
                    </div>
                  </div>}
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <label className="block text-sm font-medium mb-2" htmlFor="expense-notes">
                    Notes <span className="text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <textarea
                    id="expense-notes"
                    maxLength={500}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Add a note about this expense"
                    rows={3}
                    className="w-full px-4 py-2.5 bg-input border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                  />
                  <p className="text-xs text-muted-foreground mt-1.5 text-right">
                    {formData.notes.length}/500
                  </p>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <label className="block text-sm font-medium mb-2" htmlFor="expense-date">
                    Date
                  </label>
                  <Popover open={datePickerOpen} onOpenChange={setDatePickerOpen}>
                    <PopoverTrigger asChild>
                      <button
                        id="expense-date"
                        type="button"
                        className="w-full inline-flex items-center gap-3 px-4 py-2.5 bg-input border border-border rounded-lg text-left hover:bg-muted transition-colors focus:outline-none focus:ring-2 focus:ring-ring"
                      >
                        <CalendarDays className="w-5 h-5 text-primary" />
                        <span>{formatExpenseDate(formData.date)}</span>
                      </button>
                    </PopoverTrigger>
                    <PopoverContent align="start" className="w-auto p-0 overflow-hidden">
                      <Calendar
                        mode="single"
                        selected={parseExpenseDate(formData.date)}
                        onSelect={(selectedDate) => {
                          if (!selectedDate) return;
                          const localDate = new Date(
                            selectedDate.getTime() - selectedDate.getTimezoneOffset() * 60000,
                          ).toISOString().slice(0, 10);
                          setFormData({ ...formData, date: localDate });
                          setDatePickerOpen(false);
                        }}
                        disabled={{ after: parseExpenseDate(getToday()) }}
                        defaultMonth={parseExpenseDate(formData.date)}
                        captionLayout="dropdown"
                        fromYear={new Date().getFullYear() - 10}
                        toYear={new Date().getFullYear()}
                      />
                    </PopoverContent>
                  </Popover>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    Choose today or a previous day.
                  </p>
                </motion.div>
                <motion.div 
                  className="flex gap-3 pt-2"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                >
                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => {
                      setShowForm(false);
                      setEditingExpense(null);
                    }}
                    className="flex-1 px-4 py-2.5 border border-border rounded-lg font-medium hover:bg-muted transition-colors"
                  >
                    Cancel
                  </motion.button>
                  <motion.button
                    type="submit"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    disabled={submitting || !formData.amount}
                    className="flex-1 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
                  >
                    {submitting ? (
                      <motion.span
                        animate={{ opacity: [1, 0.5, 1] }}
                        transition={{ repeat: Infinity, duration: 1 }}
                      >
                        {editingExpense ? "Saving..." : "Adding..."}
                      </motion.span>
                    ) : (
                      editingExpense ? "Save Changes" : "Add Expense"
                    )}
                  </motion.button>
                </motion.div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Expense Confirmation */}
      <AnimatePresence>
        {pendingDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setPendingDelete(null)}
          >
            <motion.div
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(event) => event.stopPropagation()}
              className="bg-card rounded-xl border border-border shadow-lg w-full max-w-md p-6"
            >
              <div className="flex items-start gap-4">
                <div className="rounded-full bg-destructive/10 p-3 text-destructive">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h2 className="text-lg font-semibold">Delete expense?</h2>
                      <p className="text-sm text-muted-foreground mt-1">
                        This action cannot be undone.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setPendingDelete(null)}
                      aria-label="Close delete confirmation"
                      className="p-1 text-muted-foreground hover:bg-muted rounded-lg transition-colors"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <div className="mt-4 rounded-lg bg-muted/60 px-4 py-3">
                    <p className="font-medium">{pendingDelete.Category}</p>
                    <p className="text-sm text-muted-foreground">
                      {pendingDelete.Date} • ₹{pendingDelete.Amount.toLocaleString()}
                    </p>
                  </div>
                  <div className="flex gap-3 pt-5">
                    <button
                      type="button"
                      onClick={() => setPendingDelete(null)}
                      className="flex-1 px-4 py-2.5 border border-border rounded-lg font-medium hover:bg-muted transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={confirmDelete}
                      className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-destructive text-destructive-foreground rounded-lg font-medium hover:bg-destructive/90 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filter & Stats */}
      <motion.div 
        className="grid gap-4 md:grid-cols-3"
        variants={containerVariants}
      >
        <motion.div 
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          className="bg-card rounded-xl border border-border p-4 shadow-sm"
        >
          <div className="flex items-center gap-2 text-muted-foreground mb-2">
            <Filter className="w-4 h-4" />
            <span className="text-sm font-medium">Filter by Category</span>
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="w-full px-3 py-2 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-ring text-sm transition-shadow"
          >
            <option value="All">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </motion.div>

        <motion.div 
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          className="bg-card rounded-xl border border-border p-4 shadow-sm"
        >
          <p className="text-sm text-muted-foreground">Total Expenses</p>
          <motion.p 
            className="text-2xl font-bold mt-1"
            key={totalFiltered}
            initial={{ scale: 1.2, color: "oklch(0.55 0.18 155)" }}
            animate={{ scale: 1, color: "inherit" }}
            transition={{ type: "spring" }}
          >
            ₹{totalFiltered.toLocaleString()}
          </motion.p>
        </motion.div>

        <motion.div 
          variants={itemVariants}
          whileHover={{ scale: 1.02 }}
          className="bg-card rounded-xl border border-border p-4 shadow-sm"
        >
          <p className="text-sm text-muted-foreground">Transactions</p>
          <motion.p 
            className="text-2xl font-bold mt-1"
            key={filteredExpenses.length}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring" }}
          >
            {filteredExpenses.length}
          </motion.p>
        </motion.div>
      </motion.div>

      {/* Chart & List */}
      <motion.div 
        className="grid gap-6 lg:grid-cols-2"
        variants={containerVariants}
      >
        {/* Pie Chart */}
        <motion.div 
          variants={itemVariants}
          whileHover={{ scale: 1.01 }}
          className="bg-card rounded-xl border border-border p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-4">Category Breakdown</h3>
          {categoryData.length > 0 ? (
            <div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                      animationBegin={0}
                      animationDuration={800}
                    >
                      {categoryData.map((_, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={COLORS[index % COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => [`₹${value.toLocaleString()}`, "Amount"]}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <motion.div 
                className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 mt-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                {categoryData.map((item, index) => (
                  <motion.div 
                    key={item.name} 
                    className="flex items-center gap-2 leading-none"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.05 }}
                  >
                    <div
                      className="w-3 h-3 shrink-0 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm">{item.name}</span>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-muted-foreground">
              No data to display
            </div>
          )}
        </motion.div>

        {/* Expense List */}
        <motion.div 
          variants={itemVariants}
          className="bg-card rounded-xl border border-border p-6 shadow-sm"
        >
          <h3 className="font-semibold mb-4">Expense History</h3>
          {filteredExpenses.length > 0 ? (
            <div className="space-y-2 max-h-80 overflow-y-auto">
              <AnimatePresence>
                {filteredExpenses
                  .slice()
                  .reverse()
                  .map((expense, idx) => (
                    <motion.div
                      key={expense.Id || idx}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: idx * 0.03 }}
                      whileHover={{ 
                        scale: 1.02, 
                        backgroundColor: "rgba(0,0,0,0.02)",
                      }}
                      className="flex items-center justify-between p-3 bg-muted/50 rounded-lg cursor-default"
                    >
                      <div className="flex items-center gap-3">
                        <motion.div 
                          whileHover={{ rotate: 15, scale: 1.1 }}
                          className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center"
                        >
                          <Receipt className="w-5 h-5 text-primary" />
                        </motion.div>
                        <div>
                          <p className="font-medium">{expense.Category}</p>
                          <p className="text-xs text-muted-foreground">
                            {expense.Date} • {expense.Month}
                          </p>
                          {expense.Notes && (
                            <p className="text-xs text-muted-foreground mt-1 max-w-55 truncate" title={expense.Notes}>
                              {expense.Notes}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <p className="font-semibold">₹{expense.Amount.toLocaleString()}</p>
                        <motion.button
                          type="button"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => startEditing(expense)}
                          aria-label={`Edit ${expense.Category} expense`}
                          title="Edit expense"
                          className="p-2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                        >
                          <Pencil className="w-4 h-4" />
                        </motion.button>
                        <motion.button
                          type="button"
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => setPendingDelete(expense)}
                          disabled={deletingId === expense.Id}
                          aria-label={`Delete ${expense.Category} expense`}
                          title="Delete expense"
                          className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors disabled:opacity-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </motion.button>
                      </div>
                    </motion.div>
                  ))}
              </AnimatePresence>
            </div>
          ) : (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-72 flex flex-col items-center justify-center text-muted-foreground"
            >
              <motion.div
                animate={{ y: [0, -5, 0] }}
                transition={{ repeat: Infinity, duration: 2 }}
              >
                <Receipt className="w-12 h-12 mb-3 opacity-50" />
              </motion.div>
              <p>No expenses recorded</p>
              <p className="text-sm">Add your first expense to get started</p>
            </motion.div>
          )}
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
