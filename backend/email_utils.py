# backend/email_utils.py

import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Gmail App Password


def send_certificate_email(
    to_email,
    student_name,
    course_name,
    explorer_url,
    attachment_path,
    tx_hash=None
):
    """
    Sends certificate email with attached PNG/PDF.
    Includes transaction hash for easy copy/paste.
    """

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise Exception("Missing EMAIL_ADDRESS or EMAIL_PASSWORD in .env")

    # Fallback if tx_hash missing
    tx_hash_display = tx_hash if tx_hash else "Not Available"

    msg = EmailMessage()
    msg["Subject"] = "Your Credlytic Blockchain Certificate"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    # -------- TEXT VERSION --------
    msg.set_content(f"""
Hello {student_name},

Your certificate for "{course_name}" has been successfully issued.

Blockchain Explorer:
{explorer_url}

Transaction Hash:
{tx_hash_display}

Your certificate file is attached.

Regards,
Credlytic Team
""")

    # -------- HTML VERSION --------
    msg.add_alternative(f"""
<html>
  <body>
    <p>Hello <strong>{student_name}</strong>,</p>

    <p>Your certificate for <strong>{course_name}</strong> has been issued.</p>

    <p>
      <strong>Blockchain Explorer:</strong><br>
      <a href="{explorer_url}" target="_blank">{explorer_url}</a>
    </p>

    <p>
      <strong>Transaction Hash:</strong><br>
      <code style="padding:6px 10px; background:#f2f2f2; border-radius:6px;">
        {tx_hash_display}
      </code>
    </p>

    <p>Your certificate file is attached.</p>

    <p>Regards,<br>
       <strong>Credlytic Team</strong></p>
  </body>
</html>
""", subtype="html")

    # -------- ATTACHMENT --------
    with open(attachment_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(attachment_path)

        # If user sends PDF, detect and attach properly.
        subtype = "png" if file_name.lower().endswith(".png") else "pdf"

        msg.add_attachment(
            file_data,
            maintype="application" if subtype == "pdf" else "image",
            subtype=subtype,
            filename=file_name
        )

    # -------- SEND EMAIL --------
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"📧 Email sent to {to_email} with attachment {attachment_path}")
    return True
