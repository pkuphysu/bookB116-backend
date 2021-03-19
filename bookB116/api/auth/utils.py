from logging import getLogger
import random
from smtplib import SMTPDataError

from flask import abort

from .emails import send_vercode
from bookB116.settings import CONFIG


__all__ = ['get_send_vercode']
logger = getLogger(__name__)


def get_send_vercode(raw_stu_id: str, system_name: str = '主动学习实验室预约系统'):
    if CONFIG.FLASK.TESTING:
        vercode = '1000'
    else:
        vercode = str(random.SystemRandom().randint(1000, 9999))
    try:
        send_vercode(raw_stu_id, vercode, system_name)
        logger.info('Sent code %s to student %s', vercode, raw_stu_id)
    except SMTPDataError as e:
        logger.error('Mail not sent with error %s', e.smtp_error)
        abort(503, 'Mail not sent')
    return vercode
