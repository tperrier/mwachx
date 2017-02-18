#Email Imports
import smtplib,sys
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#Django imports
from django.conf import settings

def send(to,message):
    success = email("SMS as Email: {}".format(to),message)
    return 'Email Transport ID', success, {}

def email(subject,message,to='default'):
    email_settings = getattr(settings,'EMAIL_SETUP',None)
    if not isinstance(email_settings,dict):
        print "Email Settings",email_settings
        return False

    from_address = email_settings.get('from')
    to = email_settings.get('to').get(to)
    password = email_settings.get('password')
    username = email_settings.get('username')
    server = email_settings.get('server')
    if from_address is None or to is None or password is None or username is None or server is None:
        print "Email Settings Options", from_address, to, password, username, password
        return False

    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to
    msg['Subject'] = "[MX Server] {}".format(subject)
    msg.attach(MIMEText(message,'html'))

    mail_server = smtplib.SMTP(server,587)
    mail_server.ehlo(); mail_server.starttls(); mail_server.ehlo()

    mail_server.login(username,password)
    mail_server.sendmail(msg['From'],msg['To'].split(','),msg.as_string())

    mail_server.close()

    return True
