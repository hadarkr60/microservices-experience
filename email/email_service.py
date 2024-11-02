from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os


app = Flask(__name__)

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

def send_email(to_email, subject, body):
    """
    Function to send an email via Gmail SMTP.
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = to_email

    try:
        # Connect to Gmail's SMTP server and send email
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route("/sendEmail", methods=["POST"])
def send_email_endpoint():
    """
    Endpoint to receive email data and trigger the send_email function.
    Expects JSON data with "email", "location", and "temperature".
    """
    data = request.json
    to_email = data.get("email")
    location = data.get("location")
    temperature = data.get("temperature")

    if not to_email or not location or temperature is None:
        return jsonify({"error": "Invalid data provided."}), 400

    subject = f"Weather Update for {location}"
    body = f"The average temperature in {location} for the next week is {temperature}°."

    if send_email(to_email, subject, body):
        return jsonify({"message": "Email sent successfully!"}), 200
    else:
        return jsonify({"message": "Failed to send email"}), 500

if __name__ == "__main__":
    app.run(port=5001)
