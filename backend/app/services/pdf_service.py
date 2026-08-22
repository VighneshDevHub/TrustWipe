"""
Certificate PDF generation.

Turns a signed wipe record into the actual document a device owner would
hand to a buyer, refurbisher, or auditor: human-readable device/wipe
details, plus a QR code that links straight to the live verification
endpoint so anyone can independently re-check authenticity without
having to trust the PDF itself. The PDF is a convenience artifact — the
QR link is what actually carries trust.
"""
import io

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.config import get_settings

settings = get_settings()

PAGE_WIDTH, PAGE_HEIGHT = A4


def _build_qr_image(verify_url: str) -> io.BytesIO:
    """Generate a QR code PNG (in-memory) pointing at the verification URL."""
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_certificate_pdf(certificate: dict) -> bytes:
    """`certificate` is the same dict shape as CertificateOut (see
    app/schemas/wipe.py). Returns raw PDF bytes ready to stream or save.
    """
    verify_url = f"{settings.PUBLIC_BASE_URL}/verify/{certificate['certificate_id']}"
    qr_buffer = _build_qr_image(verify_url)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    margin = 20 * mm
    y = PAGE_HEIGHT - margin

    # --- Header ---
    c.setFillColor(colors.HexColor("#1a1a2e"))
    c.rect(0, PAGE_HEIGHT - 35 * mm, PAGE_WIDTH, 35 * mm, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, PAGE_HEIGHT - 18 * mm, "CERTIFICATE OF SECURE DATA ERASURE")
    c.setFont("Helvetica", 10)
    c.drawString(margin, PAGE_HEIGHT - 26 * mm, "Issued by TrustWipe — NIST SP 800-88 Compliant")

    y = PAGE_HEIGHT - 50 * mm

    # --- Device / wipe details table ---
    c.setFillColor(colors.black)
    rows = [
        ("Certificate ID", certificate["certificate_id"]),
        ("Device Serial", certificate["device_serial"]),
        ("Device Model", certificate["device_model"]),
        ("Device Type", certificate["device_type"]),
        ("Wipe Method", certificate["wipe_method"]),
        ("Started At (UTC)", str(certificate["started_at"])),
        ("Completed At (UTC)", str(certificate["completed_at"])),
        ("Verification Passed", "YES" if certificate["verification_passed"] else "NO"),
        ("Operator", certificate["operator"]),
        ("Ledger Sequence #", str(certificate["ledger_sequence_number"])),
    ]

    label_x = margin
    value_x = margin + 55 * mm
    row_height = 9 * mm

    for label, value in rows:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(label_x, y, f"{label}:")
        c.setFont("Helvetica", 10)
        # Truncate very long values (like hashes) so they don't overflow the page
        display_value = value if len(value) <= 60 else value[:57] + "..."
        c.drawString(value_x, y, display_value)
        y -= row_height

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(label_x, y, "Report Hash (SHA-256):")
    y -= 5 * mm
    c.setFont("Courier", 8)
    c.drawString(label_x, y, certificate["report_hash"])

    y -= 8 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(label_x, y, "Digital Signature (ECDSA, hex-encoded, truncated):")
    y -= 5 * mm
    c.setFont("Courier", 7)
    sig = certificate["signature"]
    c.drawString(label_x, y, sig[:80] + ("..." if len(sig) > 80 else ""))

    # --- QR code + verification note ---
    qr_size = 45 * mm
    qr_x = PAGE_WIDTH - margin - qr_size
    qr_y = 30 * mm

    from reportlab.lib.utils import ImageReader
    c.drawImage(
        ImageReader(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size,
        preserveAspectRatio=True,
    )
    c.setFont("Helvetica", 8)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 6 * mm, "Scan to verify authenticity")

    # --- Footer ---
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.grey)
    c.drawString(
        margin, 15 * mm,
        f"Verify independently at: {verify_url}"
    )
    c.drawString(
        margin, 10 * mm,
        "This certificate is cryptographically signed. Any alteration to the underlying "
        "record will cause verification to fail."
    )

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()
