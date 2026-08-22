"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCertificatePdfUrl, listCertificates, UnauthorizedError } from "@/lib/api";
import { getToken, logout } from "@/lib/auth";
import type { Certificate } from "@/lib/types";

function StatusBadge({ passed }: { passed: boolean }) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium ${
        passed ? "bg-green-100 text-trust-green" : "bg-red-100 text-trust-red"
      }`}
    >
      {passed ? "Verified" : "Failed"}
    </span>
  );
}

function toCsv(certificates: Certificate[]): string {
  const headers = [
    "certificate_id", "device_serial", "device_model", "device_type",
    "wipe_method", "started_at", "completed_at", "verification_passed",
    "operator",
  ];
  const rows = certificates.map((c) =>
    headers.map((h) => JSON.stringify((c as any)[h] ?? "")).join(",")
  );
  return [headers.join(","), ...rows].join("\n");
}

function downloadCsv(certificates: Certificate[]) {
  const csv = toCsv(certificates);
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `trustwipe-export-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function DashboardPage() {
  const [certificates, setCertificates] = useState<Certificate[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }

    listCertificates()
      .then(setCertificates)
      .catch((err) => {
        if (err instanceof UnauthorizedError) {
          logout();
          router.push("/login");
        } else {
          setError(err instanceof Error ? err.message : "Failed to load data");
        }
      });
  }, [router]);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-trust-navy">
              Recycler Dashboard
            </h1>
            <p className="text-sm text-gray-500">
              All devices processed and certified
            </p>
          </div>
          <div className="flex gap-2">
            {certificates && certificates.length > 0 && (
              <button
                onClick={() => downloadCsv(certificates)}
                className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50"
              >
                Export CSV
              </button>
            )}
            <button
              onClick={handleLogout}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50"
            >
              Log Out
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-yellow-400 bg-yellow-50 p-4 text-sm text-yellow-700">
            {error}
          </div>
        )}

        {certificates === null && !error && (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
            Loading devices…
          </div>
        )}

        {certificates !== null && certificates.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-500">
            No devices wiped yet. Run the wipe agent against a device to see
            it appear here.
          </div>
        )}

        {certificates !== null && certificates.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-3">Device</th>
                  <th className="px-4 py-3">Serial</th>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Completed</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Certificate</th>
                </tr>
              </thead>
              <tbody>
                {certificates.map((c) => (
                  <tr key={c.certificate_id} className="border-t border-gray-100">
                    <td className="px-4 py-3">{c.device_model}</td>
                    <td className="px-4 py-3 font-mono text-xs">{c.device_serial}</td>
                    <td className="px-4 py-3">{c.wipe_method}</td>
                    <td className="px-4 py-3">
                      {new Date(c.completed_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge passed={c.verification_passed} />
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={getCertificatePdfUrl(c.certificate_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-trust-navy underline"
                      >
                        View PDF
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
