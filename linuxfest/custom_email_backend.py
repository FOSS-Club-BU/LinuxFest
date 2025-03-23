from django.core.mail.backends.smtp import EmailBackend
import os


class CustomEmailBackend(EmailBackend):
    def send_messages(self, email_messages):
        for message in email_messages:
            if message.to and any(recipient.endswith('@bennett.edu.in') for recipient in message.to):
                # Use separate SMTP server for bennett.edu.in domain
                print('Using Bennett SMTP server')
                self.host = 'smtp-mail.outlook.com'
                self.port = 587
                self.username = os.getenv('BENNETT_SMTP_USER')
                self.password = os.getenv('BENNETT_SMTP_PASSWORD')
                self.use_tls = True
                self.use_ssl = False
                message.from_email = "FOSS Club <foss@bennett.edu.in>"
            else:
                print('Using default SMTP server')
                message.from_email = "Linux Fest <admin@linuxfest.fossbu.co>"
                # Use default SMTP server
                self.host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
                self.port = 587
                self.username = os.environ.get('EMAIL_HOST_USER', '')
                self.password = os.environ.get('EMAIL_HOST_PASSWORD', '')
                self.use_tls = False
            super().send_messages([message])