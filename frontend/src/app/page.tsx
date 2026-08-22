"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const [certId, setCertId] = useState("");
  const router = useRouter();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = certId.trim();
    if (trimmed) {
      router.push(`/verify/${trimmed}`);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md text-center">
        <h1 className="text-3xl font-bold text-trust-navy">TrustWipe</h1>
        <p className="mt-2 text-gray-500">
          Verify a secure data-erasure certificate
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-3">
          <input
            type="text"
            value={certId}
            onChange={(e) => setCertId(e.target.value)}
            placeholder="Enter certificate ID"
            className="rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-trust-navy focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-lg bg-trust-navy px-4 py-3 text-sm font-medium text-white hover:opacity-90"
          >
            Verify Certificate
          </button>
        </form>

        <p className="mt-6 text-xs text-gray-400">
          Or scan the QR code on a physical certificate to jump straight here.
        </p>
      </div>
    </main>
  );
}
