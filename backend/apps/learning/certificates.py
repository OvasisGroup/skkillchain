import io

import qrcode
from django.core.files.base import ContentFile
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import Certificate

TEAL = HexColor("#2dd4bf")
INK = HexColor("#0f172a")
MUTED = HexColor("#64748b")


def _student_name(certificate: Certificate) -> str:
    student = certificate.enrollment.student
    profile = student.profile
    full_name = f"{profile.first_name} {profile.last_name}".strip()
    return full_name or student.email


def render_certificate_pdf(certificate: Certificate) -> bytes:
    course_title = certificate.enrollment.course.title
    student_name = _student_name(certificate)
    issued_date = certificate.issued_at.strftime("%B %-d, %Y")

    qr_img = qrcode.make(certificate.qr_payload)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    buffer = io.BytesIO()
    page_size = landscape(A4)
    width, height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size)

    pdf.setStrokeColor(TEAL)
    pdf.setLineWidth(3)
    pdf.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm)

    pdf.setFont("Helvetica", 14)
    pdf.setFillColor(MUTED)
    pdf.drawCentredString(width / 2, height - 35 * mm, "SkillChain")

    pdf.setFont("Helvetica-Bold", 30)
    pdf.setFillColor(INK)
    pdf.drawCentredString(width / 2, height - 55 * mm, "Certificate of Completion")

    pdf.setFont("Helvetica", 13)
    pdf.setFillColor(MUTED)
    pdf.drawCentredString(width / 2, height - 75 * mm, "This certifies that")

    pdf.setFont("Helvetica-Bold", 24)
    pdf.setFillColor(TEAL)
    pdf.drawCentredString(width / 2, height - 90 * mm, student_name)

    pdf.setFont("Helvetica", 13)
    pdf.setFillColor(MUTED)
    pdf.drawCentredString(width / 2, height - 105 * mm, "has successfully completed")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(INK)
    pdf.drawCentredString(width / 2, height - 118 * mm, course_title)

    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(MUTED)
    pdf.drawCentredString(width / 2, 28 * mm, f"Issued {issued_date}")
    pdf.drawCentredString(width / 2, 22 * mm, f"Certificate ID: {certificate.certificate_uid}")

    qr_size = 26 * mm
    pdf.drawImage(
        ImageReader(qr_buffer),
        width - 12 * mm - qr_size - 8 * mm,
        14 * mm,
        width=qr_size,
        height=qr_size,
        mask="auto",
    )
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(MUTED)
    pdf.drawCentredString(width - 12 * mm - qr_size / 2 - 8 * mm, 12 * mm, "Scan to verify")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def ensure_certificate_pdf(certificate: Certificate) -> None:
    """Generates and attaches the PDF if it isn't already there — called at
    issuance time, and as a self-heal on every read for certificates issued
    before this field existed (or whose render previously failed)."""
    if certificate.pdf_file:
        return
    pdf_bytes = render_certificate_pdf(certificate)
    certificate.pdf_file.save(
        f"{certificate.certificate_uid}.pdf", ContentFile(pdf_bytes), save=True
    )
