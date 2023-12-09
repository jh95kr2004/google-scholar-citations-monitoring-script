import logging
import smtplib
from email.message import EmailMessage
from typing import BinaryIO, List, Tuple
from .sender import Sender, SenderType


class Gmail(Sender):
    def __init__(self, sender_id: str, sender_pw: str, logger: logging.Logger):
        super().__init__(SenderType.GMAIL)
        self.smtp_url = "smtp.gmail.com"
        self.smtp_tls_port = 587
        self.id = sender_id
        self.pw = sender_pw
        self.logger = logger
        self.smtp = None
        self.login()

    def __del__(self):
        self.quit()

    def login(self):
        self.quit()

        try:
            self.smtp = smtplib.SMTP(self.smtp_url, self.smtp_tls_port)
            self.smtp.starttls()
            self.smtp.login(self.id, self.pw)
        except Exception as e:
            self.logger.error("Failed to login gmail: %s", str(e))

    def quit(self):
        if self.smtp:
            try:
                self.smtp.quit()
            except:
                # ignore exception
                pass

    def send(
        self,
        subject: str = "",
        content: str = "",
        attachments: List[Tuple[str, str, str, BinaryIO]] = [],
        receiver: List[str] = [],
    ):
        if not self.is_connected():
            self.login()

        try:
            msg = EmailMessage()
            msg.set_content(content)
            msg["From"] = self.id
            msg["To"] = ", ".join(receiver)
            msg["Subject"] = subject

            for filename, maintype, subtype, fp in attachments:
                data = fp.read()
                msg.add_attachment(
                    data, maintype=maintype, subtype=subtype, filename=filename
                )

            self.smtp.send_message(msg)
        except Exception as e:
            self.logger.error("Failed to send email through gmail: %s", str(e))

    def is_connected(self):
        try:
            return self.smtp.noop()[0] == 250
        except:
            return False
