import imaplib
import email
import re
from bs4 import BeautifulSoup
from email.header import decode_header, make_header
from email.utils import parseaddr
from flask import url_for, Flask
import smtplib
from email.message import EmailMessage
import logging

# Configure logging to output debug messages to the console.
logging.basicConfig(level=logging.WARNING, format='[DEBUG] %(message)s')

import hmac, hashlib, base64

# Use a strong secret key (keep it secret!)
NFC_SECRET_KEY = b"a3dcb4d229de6fde0db5686dee47145d"

def generate_nfc_token(user_id):
    """
    Given a user_id, generate an NFC token by computing an HMAC-SHA256,
    then returning a URL-safe base64-encoded token.
    """
    h = hmac.new(NFC_SECRET_KEY, msg=user_id.encode(), digestmod=hashlib.sha256)
    token = base64.urlsafe_b64encode(h.digest()).decode().rstrip("=")
    return token


# Email configuration for IMAP
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
USERNAME = "patrick.manuel.goerner@gmail.com"
PASSWORD = "acpx xsyd wugd eiwh"
SUBJECT_FILTER = "du hast eine zahlung erhalten"
LIMIT_MSGS = 30
RECIPIENT_NAME = "Patrick Manuel Görner"

# SMTP configuration (using Gmail's SMTP server)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = USERNAME  # reusing your Gmail address
SMTP_PASSWORD = PASSWORD  # use an app-specific password if required

# Create a minimal Flask app for URL generation.
app = Flask(__name__)
app.config['SERVER_NAME'] = 'example.com'  # update this to your domain if necessary

def send_confirmation_email(user):
    """
    Sends an email confirmation message to the user.
    The email contains a link with a verification token.
    """
    try:
        with app.app_context():
            # Generate the full URL for verification.
            verification_link = url_for("verify_email", token=user["verification_token"], _external=True)
            logging.debug(f"Generated verification link: {verification_link}")

        # Create the email message.
        msg = EmailMessage()
        msg["Subject"] = "Please Confirm Your Email Address"
        msg["From"] = SMTP_USERNAME
        msg["To"] = user["email"]
        msg.set_content(f"""\
Hello {user['first_name']} {user['last_name']},

Thank you for registering.

Please confirm your email address by clicking on the link below:
{verification_link}

If you did not register, please ignore this email.
""")
        logging.debug("Email message created. Connecting to SMTP server...")

        # Connect to the SMTP server and send the message.
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            logging.debug(f"Logging in as: {SMTP_USERNAME}")
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            logging.debug("Login successful. Sending email...")
            smtp.send_message(msg)
            logging.debug(f"Confirmation email successfully sent to {user['email']}")
    except Exception as e:
        logging.exception("Failed to send confirmation email:")

def decode_mime_words(s):
    try:
        decoded = str(make_header(decode_header(s)))
        logging.debug(f"Decoded MIME words: {s} -> {decoded}")
        return decoded
    except Exception as e:
        logging.exception("Error decoding MIME words:")
        return s

def extract_reference(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        # Look for a <p> tag whose style includes 'font-size:26px' and 'font-weight:500'
        candidate = soup.find("p", style=lambda s: s and "font-size:26px" in s and "font-weight:500" in s)
        if candidate:
            ref = candidate.get_text(strip=True)
            logging.debug(f"Extracted reference: {ref}")
            return ref
    except Exception as e:
        logging.exception("Error extracting reference:")
    return ""


def extract_amount(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        match = re.search(r"hat dir\s+(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+))\s*€", text, re.IGNORECASE)
        if match:
            amount = match.group(1)
            logging.debug(f"Extracted amount: {amount}")
            return amount
    except Exception as e:
        logging.exception("Error extracting amount:")
    return ""

def extract_sender_name(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(" ", strip=True)
        matches = re.findall(r"([A-ZÄÖÜ][\w\s\-\u00C0-\u00FF]+?)\s+hat dir", text)
        for name in matches:
            name_clean = name.strip().rstrip(",")
            if name_clean != RECIPIENT_NAME:
                logging.debug(f"Extracted sender name: {name_clean}")
                return name_clean
    except Exception as e:
        logging.exception("Error extracting sender name:")
    return ""

from datetime import datetime, timedelta

def search_emails(days=1):
    results = []
    try:
        logging.debug("Connecting to IMAP server...")
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(USERNAME, PASSWORD)
        mail.select("INBOX")
        # Calculate the date string for 'days' ago.
        date_since = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
        logging.debug(f"Searching for emails SINCE {date_since} with subject: {SUBJECT_FILTER}")
        status, data = mail.search(None, f'(SINCE "{date_since}" SUBJECT "{SUBJECT_FILTER}")')
        if status != "OK":
            logging.debug(f"IMAP search error: {status}")
            mail.logout()
            return results
        email_ids = data[0].split()
        if not email_ids:
            logging.debug("No emails found.")
            mail.logout()
            return results
        email_ids = email_ids[-LIMIT_MSGS:]
        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                logging.debug(f"Failed to fetch email id: {eid}")
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject", "")
            if SUBJECT_FILTER not in subject.lower():
                continue
            raw_from = msg.get("From", "")
            header_sender_name, sender_email = parseaddr(raw_from)
            header_sender_name = decode_mime_words(header_sender_name)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                        break
                if not body:
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            charset = part.get_content_charset() or "utf-8"
                            body = part.get_payload(decode=True).decode(charset, errors="replace")
                            break
            else:
                charset = msg.get_content_charset() or "utf-8"
                body = msg.get_payload(decode=True).decode(charset, errors="replace")
            ref_extracted = extract_reference(body)
            amount_extracted = extract_amount(body)
            extracted_sender = extract_sender_name(body)
            email_info = {
                "msg_id": eid.decode() if isinstance(eid, bytes) else str(eid),
                "sender_name": header_sender_name,
                "sender_email": sender_email,
                "extracted_sender": extracted_sender,
                "subject": subject,
                "date": msg.get("Date", ""),
                "ref": ref_extracted,
                "amount": amount_extracted
            }
            logging.debug(f"Fetched email: {email_info}")
            results.append(email_info)
        mail.logout()
    except Exception as e:
        logging.exception("Error during IMAP processing:")
    results.reverse()  # Most recent first
    return results

def send_password_reset_email(user):
    """
    Sends an email with a password reset link to the user.
    """
    try:
        reset_link = url_for("reset_password", token=user["reset_token"], _external=True)
        msg = EmailMessage()
        msg["Subject"] = "Reset Your Password"
        msg["From"] = SMTP_USERNAME
        msg["To"] = user["email"]
        msg.set_content(f"""\
Hello {user['first_name']} {user['last_name']},

You have requested to reset your password.
Please click on the link below to reset your password:
{reset_link}

If you did not request this, please ignore this email.
""")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)
            logging.debug(f"Password reset email sent to {user['email']}")
    except Exception as e:
        logging.exception("Failed to send password reset email:")