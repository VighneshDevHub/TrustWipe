import type { Certificate, VerificationResult } from "@/lib/types";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-gray-100 py-2 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900 text-right break-all pl-4">
        {value}
      </span>
    </div>
  );
}

export function VerificationBanner({ result }: { result: VerificationResult }) {
  const isValid = result.overall_verified;

  return (
    <div
      className={`rounded-xl border-2 p-6 text-center ${
        isValid
          ? "border-trust-green bg-green-50"
          : "border-trust-red bg-red-50"
      }`}
    >
      <div className="text-5xl mb-2">{isValid ? "✅" : "❌"}</div>
      <h2
        className={`text-xl font-bold ${
          isValid ? "text-trust-green" : "text-trust-red"
        }`}
      >
        {isValid ? "VERIFIED" : "INVALID / TAMPERED"}
      </h2>
      <p className="mt-2 text-sm text-gray-700">{result.detail}</p>

      <div className="mt-4 flex justify-center gap-6 text-xs text-gray-500">
        <span>
          Signature: {result.signature_valid ? "✅ Valid" : "❌ Invalid"}
        </span>
        <span>
          Ledger chain: {result.chain_intact ? "✅ Intact" : "❌ Broken"}
        </span>
      </div>
    </div>
  );
}

export function CertificateDetails({ certificate }: { certificate: Certificate }) {
  return (
    <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
        Device & Wipe Details
      </h3>
      <DetailRow label="Certificate ID" value={certificate.certificate_id} />
      <DetailRow label="Device Serial" value={certificate.device_serial} />
      <DetailRow label="Device Model" value={certificate.device_model} />
      <DetailRow label="Device Type" value={certificate.device_type} />
      <DetailRow label="Wipe Method" value={certificate.wipe_method} />
      <DetailRow label="Started" value={formatDate(certificate.started_at)} />
      <DetailRow label="Completed" value={formatDate(certificate.completed_at)} />
      <DetailRow label="Operator" value={certificate.operator} />
      <DetailRow
        label="Ledger Sequence #"
        value={String(certificate.ledger_sequence_number)}
      />
    </div>
  );
}
