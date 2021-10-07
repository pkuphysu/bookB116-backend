import datetime
from logging import getLogger

from flask import abort
from flask_login import current_user
from wtforms import BooleanField, IntegerField, StringField
from wtforms.validators import DataRequired, Length, NumberRange

from bookB116.database import Student
from bookB116.settings import CONFIG
from bookB116.utils.validation import AbortForm, OnlyIfNot, RequireStu, Vercode

from .database import BookRec

logger = getLogger(__name__)


class BookForm(AbortForm):
    room_id = IntegerField(validators=[
        NumberRange(0, len(CONFIG.API.BOOKING.B116ROOMS)-1,
                    message='Room Out of Range')
    ])
    start = IntegerField(validators=[DataRequired()])
    end = IntegerField(validators=[DataRequired()])
    stu1 = StringField(validators=[RequireStu()])
    stu2 = StringField(validators=[RequireStu()])
    sponsor = StringField(validators=[
        DataRequired(),
        Length(max=8, message='Sponsor too long')
    ])
    contact = StringField(validators=[
        DataRequired(),
        Length(min=11, max=11, message='Not a phone number')
    ])
    stu_num = IntegerField(validators=[
        NumberRange(min=3, max=50, message='Number of students invalid')
    ])
    description = StringField(validators=[
        DataRequired(),
        Length(max=256, message='Description too long')
    ])
    vercode = StringField(validators=[
        OnlyIfNot('test'), Vercode()])
    test = BooleanField(validators=[OnlyIfNot('vercode')])

    def custom_validate(self):
        errors = []
        room_id = self.room_id.data
        start = datetime.datetime.fromtimestamp(self.start.data)
        end = datetime.datetime.fromtimestamp(self.end.data)
        students = []
        date = start.date()
        start = start.time()
        end = end.time()
        for stu in (self.stu1, self.stu2):
            user = Student.by_raw_id(stu.data)
            booking_num = BookRec.get_stu_book_count_now(user.stu_id)
            if booking_num >= CONFIG.API.BOOKING.MAX_BOOK:
                logger.info('Try to invite %s whose number of booking is '
                            '%s, exceeding the limit', stu.data, booking_num)
                errors.append('Invitee Exceed')
            students.append(user.stu_id)
        if errors:
            return False, errors
        return True, (room_id, [self.stu1.data, self.stu2.data],
                      students, date, start, end)


class ConfirmForm(AbortForm):
    book_id = StringField(validators=[DataRequired()])
    log_verb = 'confirm'

    def custom_validate(self):
        stu_id = current_user.stu_id
        book_rec = BookRec.query.get(self.book_id.data)
        if book_rec is None:
            logger.error('%s a booking where the '
                         'booking id %s does not exist',
                         self.log_verb, self.book_id.data)
            abort(404, 'NO BOOK_ID')
        if stu_id not in book_rec.booking_stu():
            logger.error('%s a booking where he/she is not '
                         'in the booking students list', self.log_verb)
            # Should not tell others
            abort(404, 'NO BOOK_ID')
        delta = book_rec.date - datetime.date.today()
        if not (
                datetime.timedelta(CONFIG.API.BOOKING.DAY_NEAREST) <= delta
                <= datetime.timedelta(CONFIG.API.BOOKING.DAY_FARTHEST + 1)
        ):
            logger.error('%s a booking where [%s]'
                         'is not in the available range',
                         self.log_verb, delta)
            abort(403, 'EXPIRED')
        if book_rec.canceled:
            logger.error('%s a canceled record', self.log_verb)
            abort(403, 'CANCELED')
        return True, book_rec


class CancelForm(ConfirmForm):
    vercode = StringField(validators=[Vercode()])
    log_verb = 'cancel'

    def custom_validate(self):
        valid, book_rec = super().custom_validate()
        if valid:
            if current_user.stu_id != book_rec.booking_stu()[0]:
                logger.error('cancel a booking %s where he/she is not '
                             'the sponsor', self.book_id.data)
                abort(403, 'FORBIDDEN')
        return valid, book_rec
