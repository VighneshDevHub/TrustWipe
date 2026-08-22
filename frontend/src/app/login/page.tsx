"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { AuthError, login } from "@/lib/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof AuthError ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-center text-2xl font-bold text-trust-navy">
          Recycler Dashboard Login
        </h1>
        <p className="mt-1 text-center text-sm text-gray-500">
          For ITAD operators tracking wiped devices
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-3">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-trust-navy focus:outline-none"
          />
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-trust-navy focus:outline-none"
          />
          {error && <p className="text-sm text-trust-red">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-trust-navy px-4 py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {submitting ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-gray-400">
          No account yet? Register via the API directly for this MVP
          (POST /api/v1/auth/register) — a self-serve signup form is a
          natural Phase 6 addition.
        </p>
      </div>
    </main>
  );
}
