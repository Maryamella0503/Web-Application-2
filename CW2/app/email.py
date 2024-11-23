from flask_mail import Message
from flask import current_app

def send_crime_alert_email(to, body):
    from app import mail  # Delay importing mail
    msg = Message(
        "Crime Alert",
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[to]
    )
    msg.body = body
    mail.send(msg)

