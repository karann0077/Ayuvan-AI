"""Rebuild the bundled, fictional evaluation PDF. Requires reportlab locally."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build(path: Path) -> None:
    width, height = A4
    document = canvas.Canvas(str(path), pagesize=A4, pageCompression=1)
    document.setTitle("AYUVAN fictional consultation note")
    document.setAuthor("AYUVAN demonstration")
    dark = HexColor("#1F2933")
    green = HexColor("#275F4B")
    muted = HexColor("#55636C")

    document.setFillColor(white)
    document.rect(0, 0, width, height, fill=1, stroke=0)
    document.setFillColor(green)
    document.rect(0, height - 105, width, 105, fill=1, stroke=0)
    document.setFillColor(white)
    document.setFont("Helvetica-Bold", 22)
    document.drawString(48, height - 57, "AYUVAN")
    document.setFont("Helvetica", 11)
    document.drawString(48, height - 78, "Fictional consultation note")

    y = height - 145
    document.setFillColor(HexColor("#E8F3ED"))
    document.roundRect(48, y - 27, width - 96, 40, 8, fill=1, stroke=0)
    document.setFillColor(green)
    document.setFont("Helvetica-Bold", 10)
    document.drawString(61, y - 4, "SYNTHETIC DEMONSTRATION  |  NOT A PRESCRIPTION")
    y -= 75
    document.setFillColor(dark)
    document.setFont("Helvetica-Bold", 18)
    document.drawString(48, y, "Consultation summary")
    y -= 22
    document.setStrokeColor(HexColor("#D7E2DC"))
    document.line(48, y, width - 48, y)
    y -= 30
    fields = (
        ("PATIENT", "[DEMO] Records and care"),
        ("VISIT DATE", "06 November 2026"),
        ("CLINICIAN", "Dr Sample Clinician (fictional)"),
        ("REASON", "Routine discussion about seasonal nasal irritation"),
    )
    for label, value in fields:
        document.setFillColor(muted)
        document.setFont("Helvetica-Bold", 10)
        document.drawString(48, y, label)
        document.setFillColor(dark)
        document.setFont("Helvetica", 12)
        document.drawString(183, y - 1, value)
        y -= 36

    y -= 15
    document.setFillColor(green)
    document.setFont("Helvetica-Bold", 13)
    document.drawString(48, y, "Recorded follow-up plan")
    y -= 24
    document.setFillColor(dark)
    document.setFont("Helvetica", 11)
    for line in (
        "Review the concern at a later visit.",
        "Follow-up demonstration date: 22 November 2026.",
        "Medicine reminder example: review instructions from a real prescriber.",
    ):
        document.drawString(50, y, line)
        y -= 27

    y -= 23
    document.setFillColor(HexColor("#FFF0ED"))
    document.roundRect(48, y - 74, width - 96, 91, 8, fill=1, stroke=0)
    document.setFillColor(HexColor("#A64135"))
    document.setFont("Helvetica-Bold", 11)
    document.drawString(62, y - 8, "Demonstration only")
    document.setFillColor(dark)
    document.setFont("Helvetica", 10)
    document.drawString(62, y - 27,
                        "No medicine name, dose, diagnosis or treatment is authorised by this note.")
    document.drawString(62, y - 45,
                        "All names, dates and health details on this page are synthetic.")
    document.setFillColor(muted)
    document.setFont("Helvetica", 9)
    document.drawString(48, 48,
                        "AYUVAN evaluation sample  |  Generated for demonstration  |  Page 1 of 1")
    document.save()


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "app/demo_assets/evaluation_consultation.pdf"
    build(target)
    print(f"Wrote {target}")
