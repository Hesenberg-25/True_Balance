"use client";

import { FormEvent, useEffect, useState } from "react";
import { LockKeyhole, Mail, Wallet } from "lucide-react";
import { getCurrentUser, login, signup } from "@/lib/api";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const [email, setEmail] = useState<string | null>(null);
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [formEmail, setFormEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getCurrentUser()
      .then((user) => setEmail(user.email))
      .catch(() => setEmail(null))
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const user = mode === "login"
        ? await login(formEmail, password, remember)
        : await signup(formEmail, password, remember);
      setEmail(user.email);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="min-h-screen bg-background" />;
  if (email) return <>{children}</>;

  return (
    <main className="min-h-screen bg-background flex items-center justify-center p-6">
      <section className="w-full max-w-md bg-card border border-border rounded-2xl shadow-xl p-8">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-11 h-11 rounded-xl bg-primary flex items-center justify-center">
            <Wallet className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <p className="font-semibold text-xl text-accent">TrueBalance</p>
            <p className="text-sm text-muted-foreground">Your private financial space</p>
          </div>
        </div>
        <h1 className="text-2xl font-bold">{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="text-muted-foreground mt-2 mb-6">
          {mode === "login" ? "Sign in to access your expenses and budgets." : "Your data will be kept separate from every other account."}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm font-medium">
            Email address
            <div className="relative mt-2">
              <Mail className="absolute left-3 top-3 w-5 h-5 text-muted-foreground" />
              <input required type="email" value={formEmail} onChange={(event) => setFormEmail(event.target.value)} className="w-full pl-10 pr-4 py-3 bg-input border border-border rounded-lg" placeholder="you@gmail.com" />
            </div>
          </label>
          <label className="block text-sm font-medium">
            Password
            <div className="relative mt-2">
              <LockKeyhole className="absolute left-3 top-3 w-5 h-5 text-muted-foreground" />
              <input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="w-full pl-10 pr-4 py-3 bg-input border border-border rounded-lg" placeholder="At least 8 characters" />
            </div>
          </label>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />
            Keep me signed in on this device
          </label>
          {error && <p className="text-sm text-destructive" role="alert">{error}</p>}
          <button disabled={submitting} className="w-full py-3 rounded-lg bg-primary text-primary-foreground font-medium disabled:opacity-60">
            {submitting ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        <button type="button" onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }} className="w-full mt-5 text-sm text-accent hover:underline">
          {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </section>
    </main>
  );
}
