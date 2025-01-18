import smtplib
from email.mime.text import MIMEText


def email_server_login(
    sender_em,
    sender_pass
):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_em, sender_pass)
    return server

def compose_msg(
    subject,
    body,
    from_email,
    to_email
):
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    return msg

def send_email(
    sender,
    sender_pass,
    receiver,
    subject,
    body
):
    msg = compose_msg(subject, body, sender, receiver)
    try:
        server = email_server_login(sender, sender_pass)
        server.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        print(f"Message : {msg} sending failed with ERROR : {e}")
    finally:
        server.quit()