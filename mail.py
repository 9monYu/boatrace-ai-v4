import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

from config.config import APP_PASSWORD, GMAIL

_logger = logging.getLogger(__name__)


def send(subject: str, text: str):
    try:
        message = MIMEText(text)
        message["From"] = formataddr(("ふなんゆさん", GMAIL))
        message["To"] = GMAIL
        message["Subject"] = subject

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
            smtp_server.login(GMAIL, APP_PASSWORD)
            smtp_server.send_message(message)
    except Exception:
        _logger.exception("Failed to send email.")
