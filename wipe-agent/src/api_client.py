"""
Thin HTTP client for sending a completed wipe report to the Phase 1
backend. Kept separate from main.py so it can be mocked in tests without
needing a live server.
"""
import httpx


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def submit_wipe_report(self, report: dict) -> dict:
        """POSTs the report and returns the created certificate JSON.
        Raises httpx.HTTPStatusError on a non-2xx response — callers
        should surface this clearly rather than silently swallowing it,
        since a failed submission means no certificate was ever issued."""
        response = httpx.post(
            f"{self.base_url}/api/v1/wipes", json=report, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
