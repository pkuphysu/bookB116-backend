from logging import getLogger

import click

from bookB116.settings import CONFIG

from . import bp


logger = getLogger(__name__)


@bp.cli.command('send-summary')
def send_summary():
    '''
    每日清理脚本.

    包括：
    - 发送当日的汇总邮件
    - 将已过去的预约的敏感信息抹去
    '''
    import datetime

    from bookB116.api.booking.database import BookRec, SBLink
    from bookB116 import db

    from .emails import send_summary

    send_summary(BookRec.get_booking_between(
        1, CONFIG.API.BOOKING.DAY_FARTHEST
    ))
    logger.info('Successfully sent summary email')

    today = datetime.date.today()
    for book_rec in BookRec.query.filter(BookRec.date < today):
        book_rec.contact = '***********'
        db.session.add(book_rec)
        for rec in SBLink.query.filter_by(book_id=book_rec.book_id):
            rec.raw_stu_id = '***********'
            db.session.add(rec)
    db.session.commit()
    logger.info('Successfully cleared old records')


@bp.cli.command('book')
@click.option('--raw_ids', '-i', multiple=True)
@click.option('--room-id', '-r', default=0, type=click.INT, prompt=True)
@click.option('--date', '-d', type=click.DateTime(['%Y-%m-%d']), prompt=True)
@click.option('--start', '-s', type=click.DateTime(['%H:%M']), prompt=True)
@click.option('--end', '-e', type=click.DateTime(['%H:%M']), prompt=True)
@click.option('--sponsor', '-p', default='手动预约工具人', prompt=True)
@click.option('--contact', '-c', default='00000000000', prompt=True)
@click.option('--stu-num', '-n', default=3, prompt=True)
@click.option('--description', '-de', default='[手动预约]', prompt=True)
def book(**kargs):
    '''
    手动预约

    For example:
    -i 1912345678 -r 0 -d 2020-10-10 -s 10:00 -e 12:50 -p TTH
    -c 11411411411 -n 3 -de hahaha
    '''
    from .database import BookRec

    raw_ids = kargs.pop('raw_ids')
    if not raw_ids:
        logger.warning('You forgot stu ids')

    stu_ids = [(get_stu_id(raw_id), raw_id)
               for raw_id in raw_ids]

    book_id = BookRec.commit_booking(**kargs, stu_ids=stu_ids)
    for stu_id, _ in stu_ids:
        BookRec.stu_confirm(stu_id, book_id)
    BookRec.query.get(book_id).update_confirm()

    logger.info('Book success!')


def get_stu_id(raw_id):
    from bookB116.database import Student

    try:
        return Student.by_raw_id(raw_id).stu_id
    except AttributeError:
        raise click.ClickException(f'stu id {raw_id} typo!')
