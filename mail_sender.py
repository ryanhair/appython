
from google.appengine.ext.webapp import template
from google.appengine.api import mail
import os

class MailSender():

    @staticmethod
    def send_mail(recipient, sender, subject, template_name, template_values, attach=None):
        path = os.path.join(os.path.dirname(__file__), '../templates/email/{0}'.format(template_name))
        html = template.render(path, template_values)
        email = mail.EmailMessage()
        email.sender = sender
        email.to = recipient
        email.subject = subject
        email.html = html
        if attach:
            #example of attach [('new.csv', out.getvalue())]
            email.attachments=attach
        email.send()


    @staticmethod
    def send_text_message(phone, carrier, sender, subject, html):
        email = mail.EmailMessage()
        email.sender = sender
        email.to = phone + '@' + carrier
        email.subject = subject
        email.html = html
        email.send()

