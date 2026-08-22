import type { Certificate, VerificationResult } from "./types";
import { getToken } from "./auth";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class CertificateNotFoundError extends Error {}
export class UnauthorizedError extends Error {}

async function fetchJson<T>(path: string, requireAuth = false): Promise<T> {
  const headers: HeadersInit = {};
  if (requireAuth) {
    const token = getToken();
    if (!token) throw new UnauthorizedError("Not logged in");
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers,
  });
  if (res.status === 404) {
    throw new CertificateNotFoundError(`Not found: ${path}`);
  }
  if (res.status === 401) {
    throw new UnauthorizedError("Session expired, please log in again");
  }
  if (!res.ok) {
    throw new Error(`Request to ${path} failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function getCertificate(certificateId: string): Promise<Certificate> {
  return fetchJson<Certificate>(`/api/v1/certificates/${certificateId}`);
}

export async function verifyCertificate(
  certificateId: string
): Promise<VerificationResult> {
  return fetchJson<VerificationResult>(`/api/v1/verify/${certificateId}`);
}

export async function listCertificates(): Promise<Certificate[]> {
  return fetchJson<Certificate[]>(`/api/v1/certificates`, true);
}

export function getCertificatePdfUrl(certificateId: string): string {
  return `${API_BASE_URL}/api/v1/certificates/${certificateId}/pdf`;
}
