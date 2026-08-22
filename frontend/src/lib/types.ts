// Mirrors backend/app/schemas/wipe.py — keep these in sync manually for
// now; a shared OpenAPI-generated client is a good Phase 6+ upgrade.

export interface Certificate {
  certificate_id: string;
  device_serial: string;
  device_model: string;
  device_type: string;
  wipe_method: string;
  started_at: string;
  completed_at: string;
  verification_passed: boolean;
  operator: string;
  report_hash: string;
  signature: string;
  ledger_sequence_number: number;
  created_at: string;
}

export interface VerificationResult {
  certificate_id: string;
  signature_valid: boolean;
  chain_intact: boolean;
  overall_verified: boolean;
  detail: string;
}
