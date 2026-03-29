import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def generate_service_pdf(obj, status="COMPLETED"):
    """
    Generates a high-quality, professional, government-style PDF receipt 
    for Mishra Consultancy with no payment links.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- 1. Header & Branding ---
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    
    # Professional Blue Header Background
    c.setFillColor(colors.HexColor("#002d5b")) 
    c.rect(0, height - 80, width, 80, fill=1)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 45, "MISHRA CONSULTANCY")
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 60, "OFFICIAL LEGAL & TAXATION COMMAND CENTER")

    # --- 2. Receipt & Client Information ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 120, "OFFICIAL SERVICE RECEIPT")
    
    c.setFont("Helvetica", 10)
    # Professional receipt tracking: ID/Year
    c.drawString(50, height - 140, f"Receipt No: MC/REC/{obj.id}/{datetime.date.today().year}")
    c.drawString(50, height - 155, f"Date issued: {datetime.date.today().strftime('%B %d, %Y')}")
    
    # FIXED DASHED LINE LOGIC - Safe for ReportLab
    c.setDash(1, 2) 
    c.line(50, height - 165, width - 50, height - 165)
    c.setDash([]) # Correctly resets dash cycle to avoid (0,0) error

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 185, "CLIENT DETAILS:")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 200, f"Consultancy ID: {obj.client.unique_id}")
    c.drawString(50, height - 215, f"Full Name: {obj.client.user.get_full_name()}")
    c.drawString(50, height - 230, f"Registered Contact: {obj.client.phone}")

    # --- 3. Service Particulars Table ---
    # Shaded Table Header
    c.setFillColor(colors.HexColor("#f8f9fa"))
    c.rect(50, height - 280, width - 100, 25, fill=1)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, height - 273, "PARTICULARS / SERVICE DESCRIPTION")
    c.drawRightString(width - 60, height - 273, "CHARGES (INR)")

    # Dynamic Table Content
    c.setFont("Helvetica", 11)
    service_text = f"{obj.get_service_type_display()} - {obj.sub_service}"
    c.drawString(60, height - 310, service_text)
    c.drawRightString(width - 60, height - 310, f"Rs. {obj.amount}")

    # --- 4. Total Calculation ---
    c.line(width - 200, height - 340, width - 50, height - 340)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(320, height - 360, "TOTAL AMOUNT:")
    c.drawRightString(width - 60, height - 360, f"Rs. {obj.amount}")

    # --- 5. Professional Watermark ---
    c.saveState()
    c.setFont("Helvetica-Bold", 60)
    # Semi-transparent Green "OFFICIAL" stamp
    c.setStrokeColor(colors.HexColor("#d4edda"))
    c.setFillColor(colors.HexColor("#28a745"), alpha=0.1)
    label = "OFFICIAL RECEIPT"
    
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, label)
    c.restoreState()

    # --- 6. Official Footer & Declaration ---
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, 150, "DECLARATION:")
    c.setFont("Helvetica", 9)
    c.drawString(50, 135, "This document serves as proof of service completion and payment recorded at our command center.")
    c.drawString(50, 120, "For any discrepancies, please contact the Mishra Consultancy support line.")
        
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 50, "This is a computer-generated document and does not require a physical signature.")
    c.drawCentredString(width / 2, 38, "© 2026 Mishra Consultancy Ltd. All Rights Reserved.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer