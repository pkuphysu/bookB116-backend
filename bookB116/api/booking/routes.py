import datetime
from logging import getLogger

from flask import abort, request, session, jsonify
from flask_login import current_user, login_required

from bookB116 import cryptor
from bookB116.settings import CONFIG

from . import bp
from .database import BookRec
from .forms import BookForm, ConfirmForm, CancelForm

logger = getLogger(__name__)
BOOKING = CONFIG.API.BOOKING


@bp.route('/api/booking/my')
@login_required
def my_status():
    '''
    预约主页面
    '''
    logger.info('Booking Home visited')
    records = []
    for r in BookRec.get_stu_booking(current_user.stu_id):
        start_datetime = datetime.datetime.combine(r.date, r.start_time)
        end_datetime = datetime.datetime.combine(r.date, r.end_time)
        records.append({
            'id': r.book_id,
            'canceled': r.canceled,
            'confirmed': r.confirmed,
            'bookTime': int(r.book_time.timestamp()),
            'startTime': int(start_datetime.timestamp()),
            'endTime': int(end_datetime.timestamp()),
            'roomId': r.room_id,
            'description': r.description,
            'studentNumber': r.stu_num,
            'sponsor': r.sponsor,
            'confirmStatus': r.get_confirm_status()
        })
    return jsonify({
        'bookCount': BookRec.get_stu_book_count_now(current_user.stu_id),
        'bookRecords': records})


@bp.route('/api/booking/all')
@login_required
def all_status():
    return jsonify(BookRec.get_booking_info())


@bp.route('/api/booking/book', methods=['post'])
@login_required
def book():
    if BookRec.get_stu_book_count_now(current_user.stu_id) >= BOOKING.MAX_BOOK:
        # Clear session
        session.pop('vercode', None)
        logger.info('Try to initiate book exceeding limit')
        abort(409, 'Sponsor Exceeded')
    book_form = BookForm()
    room_id, raw_ids, students, date, start, end = book_form.validate()
    checking = book_form.test.data
    raw_stu_id = request.args.get('rawId')
    if not raw_stu_id or cryptor.hashit(raw_stu_id) != current_user.stu_id:
        abort(403, 'Bad Authorization')
    raw_ids = [raw_stu_id] + raw_ids
    students = [current_user.stu_id] + students
    students = list(dict((s, None) for s in students))
    # if len(students) != 3:
    #     logger.info('Duplicate invitation: %s', students)
    #     abort(400, 'Duplicate')
    if not is_valid_booking_time(room_id, date, start, end):
        # is_valid_booking_time shall handle logging stuff
        abort(400, 'Invalid Time')
    if checking:
        return jsonify(message='Vercode needed')

    book_id = BookRec.commit_booking(
        zip(students, raw_ids), room_id, date, start, end,
        book_form.sponsor.data, book_form.contact.data,
        book_form.stu_num.data, book_form.description.data)
    BookRec.stu_confirm(current_user.stu_id, book_id)
    # for stu_id in students:
    #     BookRec.stu_confirm(stu_id, book_id)
    BookRec.query.get(book_id).update_confirm()
    logger.info('Book %s initiated with %s', book_id, students)
    return jsonify(message='Successfully Booked')


@bp.route('/api/booking/cancel', methods=['POST'])
@login_required
def cancel():
    '''
    处理取消预约请求
    '''
    book_rec = CancelForm().validate()
    book_rec.cancel()
    logger.info('Book %s canceled', book_rec.book_id)
    return jsonify(message='Successfully Canceled')


@bp.route('/api/booking/confirm', methods=['POST'])
@login_required
def confirm():
    book_rec = ConfirmForm().validate()
    if is_valid_booking_time(book_rec.room_id, book_rec.date,
                             book_rec.start_time, book_rec.end_time):
        BookRec.stu_confirm(current_user.stu_id, book_rec.book_id)
        book_rec.update_confirm()
        logger.info('Confirimed book %s', book_rec.book_id)
        return jsonify(message='Successfully Confirmed')
    # 409 Conflict
    abort(409, 'Hand Too Slow')


def is_valid_booking_time(room_id, date, start, end):
    '''
    调用database中函数获取预约时间内的记录，测试所给的预约时间是否合法

    为了防止恶意攻击，这里要进行完全检测。包括但不限于：
    预约起止时间是否在开放预约时间内，时间间隔是否正常，
    是否与其他预约有交叉关系，是否处在工作世界内,
    预约时间是否精确到分
    '''
    if start > end:
        logger.info('start time [%s] is later than end time [%s]',
                    start, end)
        return False
    if not (BOOKING.WORKING_HOUR[0] <= start and
            end <= BOOKING.WORKING_HOUR[1]):
        logger.info('[%s - %s] not in the work hour',
                    start, end)
        return False
    if start.minute != 0 or end.minute != 50:
        logger.info('[%s - %s] do not match current time pattern',
                    start, end)
        return False
    # Here is the trick:
    # `time` cannot subtract `time`, and `BOOKING.LONGEST` is `Interval`,
    # which defined opertaion (`__radd__` and `__rsub__`) with `time`.
    # However, `start + BOOKING.LONGEST` may be tomorrow,
    # but `end - BOOKING.LONGEST` never will. Let's pick this
    if end - BOOKING.LONGEST > start:
        logger.info('[%s - %s] too long', start, end)
        return False
    if not (datetime.timedelta(BOOKING.DAY_NEAREST)
            <= date - datetime.date.today()
            <= datetime.timedelta(BOOKING.DAY_FARTHEST)):
        logger.info('Date [%s] out of range', date)
        return False

    bookings = BookRec.get_by_room_date(room_id, date)
    bookings.sort(key=lambda r: r.end_time)
    if not bookings or bookings[-1].end_time + BOOKING.INTERVAL < start:
        return True
    for i, booking in enumerate(bookings):
        # s e *s* s e <- booking.end_time
        if start < booking.end_time:
            if i > 0 and start < bookings[i-1].end_time + BOOKING.INTERVAL:
                logger.info('time conflict')
                return False
            # s e *s* *e* s <- booking.start_time e
            if booking.start_time - BOOKING.INTERVAL < end:
                logger.info('time conflict')
                return False
            return True
    logger.info('Unknown time error')
    return False
