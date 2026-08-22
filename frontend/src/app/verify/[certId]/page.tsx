"use client";

import { useEffect, useState } from "react";
import {
  CertificateNotFoundError,
  getCertificate,
  getCertificatePdfUrl,
  verifyCertificate,
} from "@/lib/api";
import type { Certificate, VerificationResult } from "@/lib/types";
import {
  CertificateDetails,
  VerificationBanner,
} from "@/components/VerificationResult";

type PageState =
  | { status: "loading" }
  | { status: "not_found" }
  | { status: "error"; message: string }
  | { status: "loaded"; certificate: Certificate; result: VerificationResult };

export default function VerifyPage({
  params,
}: {
  params: { certId: string };
}) {
  const [state, setState] = useState<PageState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setState({ status: "loading" });
      try {
        const [certificate, result] = await Promise.all([
          getCertificate(params.certId),
          verifyCertificate(params.certId),
        ]);
        if (!cancelled) {
          setState({ status: "loaded", certificate, result });
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof CertificateNotFoundError) {
          setState({ status: "not_found" });
        } else {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Unknown error",
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params.certId]);

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-10">
      <div className="mx-auto max-w-xl">
        <header className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-trust-navy">
            TrustWipe Verification
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Independently checking this certificate against the signed record
          </p>
        </header>

        {state.status === "loading" && (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-gray-500">
            Checking signature and ledger chain…
          </div>
        )}

        {state.status === "not_found" && (
          <div className="rounded-xl border-2 border-trust-red bg-red-50 p-6 text-center">
            <div className="text-4xl mb-2">❓</div>
            <h2 className="text-lg font-bold text-trust-red">
              Certificate Not Found
            </h2>
            <p className="mt-2 text-sm text-gray-700">
              No certificate exists with this ID. Double-check the QR code or
              certificate ID.
            </p>
          </div>
        )}

        {state.status === "error" && (
          <div className="rounded-xl border-2 border-yellow-400 bg-yellow-50 p-6 text-center">
            <h2 className="text-lg font-bold text-yellow-700">
              Couldn&apos;t reach the verification service
            </h2>
            <p className="mt-2 text-sm text-gray-700">{state.message}</p>
          </div>
        )}

        {state.status === "loaded" && (
          <>
            <VerificationBanner result={state.result} />
            <CertificateDetails certificate={state.certificate} />
            <div className="mt-4 text-center">
              <a
                href={getCertificatePdfUrl(state.certificate.certificate_id)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg bg-trust-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              >
                Download Certificate PDF
              </a>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
