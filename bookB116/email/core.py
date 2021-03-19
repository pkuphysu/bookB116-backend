# *-*coding:utf-8*-*
import os.path
import smtplib
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from bookB116.settings import CONFIG


def get_template(path, name):
    if os.path.isfile(path):
        path = os.path.dirname(path)
    return Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        loader=FileSystemLoader(path)
    ).get_template(name)


def send_email(receivers, subject, msg, mime='html',
               fromaddr=CONFIG.EMAIL.FROMADDR):
    '''send email'''
    sender, passwd = CONFIG.EMAIL.CREDENTIALS
    message = MIMEText(msg, mime, 'utf-8')
    message['From'] = formataddr((fromaddr, sender))
    if isinstance(receivers, str):
        message['To'] = receivers
    else:
        message['To'] = Header(','.join(receivers), 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    smtpObj = smtplib.SMTP_SSL(CONFIG.EMAIL.MAILHOST)
    smtpObj.login(sender, passwd)
    smtpObj.sendmail(sender, receivers, message.as_string())
    smtpObj.quit()
