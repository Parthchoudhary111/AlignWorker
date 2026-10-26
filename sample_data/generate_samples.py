import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_pdf_invoice(filename, vendor, inv_num, amount, due_date, category, desc, notes=""):
    filepath = os.path.join(SAMPLE_DIR, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter

    # Header
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(50, height - 60, vendor)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(50, height - 75, "INVOICE FOR PROFESSIONAL SERVICES")

    # Invoice Meta Box
    c.setFillColor(colors.HexColor("#f1f5f9"))
    c.roundRect(width - 240, height - 120, 190, 80, 6, fill=True, stroke=False)
    
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(width - 225, height - 65, f"Invoice #: {inv_num}")
    c.drawString(width - 225, height - 85, f"Date: 2026-10-24")
    c.drawString(width - 225, height - 105, f"Due Date: {due_date}")

    # Divider
    c.setStrokeColor(colors.HexColor("#cbd5e1"))
    c.setLineWidth(1)
    c.line(50, height - 140, width - 50, height - 140)

    # Details
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(50, height - 175, "Billed To:")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(50, height - 195, "Enterprise Operations Inc.")
    c.drawString(50, height - 210, "100 Silicon Way, Tech District")
    c.drawString(50, height - 225, "accounts@enterprise-ops.local")

    # Table Header
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(50, height - 270, width - 100, 25, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, height - 262, "Description")
    c.drawString(320, height - 262, "Category")
    c.drawString(width - 120, height - 262, "Amount (USD)")

    # Line Item
    c.setFillColor(colors.HexColor("#1e293b"))
    c.setFont("Helvetica", 10)
    c.drawString(60, height - 295, desc)
    c.drawString(320, height - 295, category)
    c.drawString(width - 120, height - 295, f"${amount:,.2f}")

    # Total Box
    c.line(50, height - 320, width - 50, height - 320)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#0f172a"))
    c.drawString(width - 240, height - 350, "Total Balance Due:")
    c.setFillColor(colors.HexColor("#2563eb"))
    c.drawString(width - 120, height - 350, f"${amount:,.2f}")

    if notes:
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor("#64748b"))
        c.drawString(50, height - 400, f"Notes: {notes}")

    c.save()
    print(f"Generated {filepath}")

if __name__ == "__main__":
    # 1. Standard Clean Invoice
    create_pdf_invoice(
        filename="invoice_acme_corp.pdf",
        vendor="Acme Corp Enterprise Solutions",
        inv_num="INV-ACME-2026-441",
        amount=4750.00,
        due_date="2026-11-20",
        category="Software Subscriptions",
        desc="Annual Cloud Workspace & API Licenses (10 seats)",
        notes="Net 30 payment terms. Wire transfer preferred."
    )

    # 2. Edge Case Invoice (European Date format DD/MM/YYYY to trigger and test Self-Correction)
    create_pdf_invoice(
        filename="invoice_apex_logistics.pdf",
        vendor="Apex Logistics & Advisory",
        inv_num="INV-APX-8802",
        amount=12450.00,
        due_date="15/12/2026", # European format!
        category="Consulting & Professional Services",
        desc="Q4 Strategic Logistics Assessment and Architecture Audit",
        notes="Urgent processing requested. High-value authorization required."
    )
