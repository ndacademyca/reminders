# -*- coding: utf-8 -*-
import os
import json
import base64
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------- GOOGLE SHEET CONFIG -----------------
SPREADSHEET_ID = "1kfrSDM1c8Z9MBtI85IjDjJABL2KXuN1k8yPyAfWKh0U"
RANGE_NAME = "Current_Report"

# ---------------- EMAIL CONFIG (Gmail) -----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # App password

# ---------------- SERVICE ACCOUNT FROM SECRET -----------------
if "SERVICE_ACCOUNT_JSON" not in os.environ:
    raise ValueError("SERVICE_ACCOUNT_JSON environment variable is not set!")

SERVICE_ACCOUNT_INFO = json.loads(
    base64.b64decode(os.environ["SERVICE_ACCOUNT_JSON"]).decode("utf-8")
)

# ---------------- LOG FUNCTION -----------------
def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ---------------- READ GOOGLE SHEET -----------------
def read_google_sheet():
    log_message("📌 read_google_sheet() called")
    try:
        creds = Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        service = build("sheets", "v4", credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()
        values = result.get("values", [])
        if not values:
            log_message("❌ No data found in Google Sheet.")
            return None
        df = pd.DataFrame(values[1:], columns=values[0])
        log_message(f"✅ Google Sheet read successfully. Rows: {len(df)}")
        return df
    except Exception as e:
        log_message(f"❌ Failed to read Google Sheet: {e}")
        return None

# ---------------- SEND EMAIL -----------------
# def send_email(recipient, subject, body):
#     try:
#         msg = MIMEMultipart()
#         # msg["From"] = EMAIL_USER
#         msg['From'] = f"New Dimension Academy <{EMAIL_USER}>"
#         msg["To"] = recipient
#         msg["Subject"] = subject
#         msg.attach(MIMEText(body, "html"))

#         context = ssl.create_default_context()
#         with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
#             server.login(EMAIL_USER, EMAIL_PASSWORD)
#             server.sendmail(EMAIL_USER, recipient, msg.as_string())

#         log_message(f"✅ Email sent to {recipient}")
#     except Exception as e:
#         log_message(f"❌ Failed to send email to {recipient}: {e}")

def send_email(to_email, teacher_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = f"New Dimension Academy <{EMAIL_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        # BCC recipients
        bcc_list = ["alhuraibia@gmail.com","dalmaznaee@gmail.com"]

        # Add teacher email to BCC if exists
        if teacher_email and str(teacher_email).strip():
            bcc_list.append(teacher_email)

        # Final recipient list (To + BCC)
        recipients = [to_email] + bcc_list

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, recipients, msg.as_string())

        log_message(
            f"Email sent → TO: {to_email} | BCC: {', '.join(bcc_list)}"
        )

    except Exception as e:
        log_message(f"❌ Failed to send email to {to_email}: {e}")

# ---------------- PROCESS REMINDERS -----------------#
def process_reminders():
    df = read_google_sheet()
    if df is None:
        return "No data to process."

    today_str = datetime.now().strftime("%Y-%m-%d")
    log_message(f"Processing reminders for {today_str}")
    sent_count = 0

    for _, row in df.iterrows():
        if row["Report_Date"] != today_str:
            continue

        body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                  <meta charset="UTF-8">
                  <title>Student Progress Report</title>
                </head>
                <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

                <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;">
                  <tr>
                    <td align="center" style="padding:20px;">

                      <!-- Main Container -->
                      <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-collapse:collapse; border-radius:8px; overflow:hidden;">

                        <!-- Header Image -->
                        <tr>
                          <td>
                            <img src="{{Header_Image_URL}}" alt="Header Image" width="600" style="display:block; width:100%; max-width:600px;">
                          </td>
                        </tr>

                        <!-- Title -->
                        <tr>
                          <td style="padding:20px; text-align:center; background-color:#f9fafb;">
                            <h2 style="margin:0; color:#2c3e50;">Student Progress Report</h2>
                            <p style="margin:6px 0 0; font-size:14px; color:#7f8c8d;">
                              {row['Course_Month']} {row['Course_Year']}
                            </p>
                          </td>
                        </tr>

                        <!-- Student Information -->
                        <tr>
                          <td style="padding:20px;">
                            <table width="100%" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
                              <tr>
                                <td width="30%" style="background-color:#eef2f5;"><strong>Student Name</strong></td>
                                <td>{row['Student_Name}']}</td>
                              </tr>
                              <tr>
                                <td style="background-color:#eef2f5;"><strong>Course</strong></td>
                                <td>{row['Course}']}</td>
                              </tr>
                              <tr>
                                <td style="background-color:#eef2f5;"><strong>Level</strong></td>
                                <td>{row['Level']}</td>
                              </tr>
                              <tr>
                                <td style="background-color:#eef2f5;"><strong>Teacher</strong></td>
                                <td>{row['Teacher']}</td>
                              </tr>
                            </table>
                          </td>
                        </tr>

                        <!-- Cognitive Goals -->
                        <tr>
                          <td style="padding:20px;">
                            <table width="100%" cellpadding="10" cellspacing="0" style="border-collapse:collapse;">
                              <tr>
                                <td style="background-color:#34495e; color:#ffffff;"><strong>Cognitive Goals</strong></td>
                              </tr>
                              <tr>
                                <td style="border:1px solid #e0e0e0; line-height:1.6;">
                                  {row['Cognitive_Goals']}
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>

                        <!-- Teacher Comments -->
                        <tr>
                          <td style="padding:20px;">
                            <table width="100%" cellpadding="10" cellspacing="0" style="border-collapse:collapse;">
                              <tr>
                                <td style="background-color:#34495e; color:#ffffff;"><strong>Teacher’s Comments</strong></td>
                              </tr>
                              <tr>
                                <td style="border:1px solid #e0e0e0; line-height:1.6;">
                                  {row['Teacher_Comments']}
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>

                        <!-- General Comment -->
                        <tr>
                          <td style="padding:20px;">
                            <table width="100%" cellpadding="10" cellspacing="0" style="border-collapse:collapse;">
                              <tr>
                                <td style="background-color:#34495e; color:#ffffff;"><strong>General Comment</strong></td>
                              </tr>
                              <tr>
                                <td style="border:1px solid #e0e0e0; line-height:1.6;">
                                  {row['General_Comment']}
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>

                        <!-- Footer Info -->
                        <tr>
                          <td style="padding:20px; text-align:center; font-size:13px; color:#7f8c8d;">
                            <p style="margin:4px 0;">Report Date: {row['Report_Date']}</p>
                            <p style="margin:4px 0;">
                              Contact: {row['Teacher']} – {row['Teacher_Email']}
                            </p>
                          </td>
                        </tr>

                        <!-- Footer Image -->
                        <tr>
                          <td>
                            <img src="{{Footer_Image_URL}}" alt="Footer Image" width="600" style="display:block; width:100%; max-width:600px;">
                          </td>
                        </tr>

                      </table>
                      <!-- End Main Container -->

                    </td>
                  </tr>
                </table>

                </body>
                </html>

                """


        teacher_email = row.get("Teacher_Email", "")

        send_email(
            to_email=row["Student_Email"],
            teacher_email=teacher_email,
            subject=f"{row['Course_Month']} {row['Course_Year']} {row['Course}']} Progress Report for {row['Student_Name']}",
            body=body
        )

        sent_count += 1

    log_message(f"🎉 All reminders processed. Total emails sent: {sent_count}")
    return f"Done — {sent_count} reminder(s) sent."

# ---------------- MAIN ENTRY POINT -----------------
if __name__ == "__main__":
    process_reminders()
















# -*- coding: utf-8 -*-

import os
import json
import base64
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# ---------------- GOOGLE SHEET CONFIG -----------------
SPREADSHEET_ID = "1kfrSDM1c8Z9MBtI85IjDjJABL2KXuN1k8yPyAfWKh0U"
RANGE_NAME = "Current_Report"

# ---------------- EMAIL CONFIG (Gmail) -----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Gmail App Password

# ---------------- IMAGE CONFIG -----------------
HEADER_IMAGE_URL = os.environ.get("HEADER_IMAGE_URL", "")
FOOTER_IMAGE_URL = os.environ.get("FOOTER_IMAGE_URL", "")

# ---------------- SERVICE ACCOUNT FROM SECRET -----------------
if "SERVICE_ACCOUNT_JSON" not in os.environ:
    raise ValueError("SERVICE_ACCOUNT_JSON environment variable is not set")

SERVICE_ACCOUNT_INFO = json.loads(
    base64.b64decode(os.environ["SERVICE_ACCOUNT_JSON"]).decode("utf-8")
)

# ---------------- LOG FUNCTION -----------------
def log_message(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ---------------- READ GOOGLE SHEET -----------------
def read_google_sheet():
    log_message("read_google_sheet() started")
    try:
        creds = Credentials.from_service_account_info(
            SERVICE_ACCOUNT_INFO,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )

        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        values = result.get("values", [])
        if not values:
            log_message("No data found in Google Sheet")
            return None

        df = pd.DataFrame(values[1:], columns=values[0]).fillna("")
        log_message(f"Google Sheet loaded successfully. Rows: {len(df)}")
        return df

    except Exception as e:
        log_message(f"Failed to read Google Sheet: {e}")
        return None

# ---------------- SEND EMAIL -----------------
def send_email(to_email: str, teacher_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = f"New Dimension Academy <{EMAIL_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # BCC list
        bcc_list = [
            "alhuraibia@gmail.com",
            "dalmaznaee@gmail.com"
        ]

        if teacher_email and str(teacher_email).strip():
            bcc_list.append(teacher_email)

        msg["Bcc"] = ", ".join(bcc_list)
        msg.attach(MIMEText(body, "html"))

        recipients = [to_email] + bcc_list

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, recipients, msg.as_string())

        log_message(f"Email sent → TO: {to_email} | BCC: {', '.join(bcc_list)}")

    except Exception as e:
        log_message(f"Failed to send email to {to_email}: {e}")

# ---------------- PROCESS REPORTS -----------------
def process_reminders():
    df = read_google_sheet()
    if df is None or df.empty:
        return "No data to process"

    today_str = datetime.now().strftime("%Y-%m-%d")
    log_message(f"Processing reports for date: {today_str}")

    sent_count = 0

    for _, row in df.iterrows():
        report_date = str(row.get("Report_Date", "")).split(" ")[0]
        if report_date != today_str:
            continue

        body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Student Progress Report</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f8;">
<tr>
<td align="center" style="padding:20px;">

<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-collapse:collapse; border-radius:8px; overflow:hidden;">

<tr>
<td>
<img src="{HEADER_IMAGE_URL}" width="600" style="display:block; width:100%;">
</td>
</tr>

<tr>
<td style="padding:20px; text-align:center; background-color:#f9fafb;">
<h2 style="margin:0;">Student Progress Report</h2>
<p>{row['Course_Month']} {row['Course_Year']}</p>
</td>
</tr>

<tr>
<td style="padding:20px;">
<table width="100%" cellpadding="8" cellspacing="0">
<tr><td><strong>Student Name</strong></td><td>{row['Student_Name']}</td></tr>
<tr><td><strong>Course</strong></td><td>{row['Course']}</td></tr>
<tr><td><strong>Level</strong></td><td>{row['Level']}</td></tr>
<tr><td><strong>Teacher</strong></td><td>{row['Teacher']}</td></tr>
</table>
</td>
</tr>

<tr>
<td style="padding:20px;">
<strong>Cognitive Goals</strong><br>
{row['Cognitive_Goals']}
</td>
</tr>

<tr>
<td style="padding:20px;">
<strong>Teacher Comments</strong><br>
{row['Teacher_Comments']}
</td>
</tr>

<tr>
<td style="padding:20px;">
<strong>General Comment</strong><br>
{row['General_Comment']}
</td>
</tr>

<tr>
<td style="padding:20px; text-align:center; font-size:13px;">
Report Date: {row['Report_Date']}<br>
Contact: {row['Teacher']} – {row['Teacher_Email']}
</td>
</tr>

<tr>
<td>
<img src="{FOOTER_IMAGE_URL}" width="600" style="display:block; width:100%;">
</td>
</tr>

</table>
</td>
</tr>
</table>

</body>
</html>
"""

        subject = (
            f"{row['Course_Month']} {row['Course_Year']} "
            f"{row['Course']} Progress Report for {row['Student_Name']}"
        )

        send_email(
            to_email=row["Student_Email"],
            teacher_email=row.get("Teacher_Email", ""),
            subject=subject,
            body=body
        )

        sent_count += 1

    log_message(f"Completed. Emails sent: {sent_count}")
    return f"Done — {sent_count} report(s) sent"

# ---------------- MAIN -----------------
if __name__ == "__main__":
    process_reminders()
