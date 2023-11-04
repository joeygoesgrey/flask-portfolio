import smtplib
import bleach
from email.message import EmailMessage
import os
from flask import current_app


def send_me_the_email(*args, **kwargs):
    message_content = kwargs.get('message', '')
    email = kwargs.get('email', '')
    full_name = kwargs.get('full_name', '')
    subject = kwargs.get('subject', '')

    message = EmailMessage()
    message.set_content(
        f"MESSAGE:{bleach.clean(message_content)}\n EMAIL:{email} \n NAME:{full_name}")
    message['Subject'] = subject.upper()
    message['From'] = email
    message['To'] = current_app.config['EMAIL']

    email_server = smtplib.SMTP("smtp.gmail.com", 587)
    email_server.starttls()
    email_server.login(current_app.config['EMAIL'], current_app.config['PASSKEY'])
    email_server.send_message(message)
