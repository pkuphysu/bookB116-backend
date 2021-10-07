import datetime

from sqlalchemy.sql import func

from bookB116 import db
from bookB116.settings import CONFIG

# DO NOT MOVE `today` HERE AS A CONST BECAUSE
# THE SERVER NEED TO RUN FOR MANY DAYS


class BookRec(db.Model):
    '''
    储存预约记录的数据库模板

    字段
    --------
    book_id: 自增字段，预约的号码
    room_id: 房间号码，到时候加一个字典翻译成人话
    book_time: 预约操作的时间，由服务端提供
    date: 预约的哪一天
    start_time: 预约开始时间
    end_time: 预约结束时间
    canceled: 是否取消
    confirmed: 是否确认成功
    '''
    __tablename__ = 'BookRec'

    book_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.SmallInteger, nullable=False)
    book_time = db.Column(db.DateTime, server_default=func.now())
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    sponsor = db.Column(db.Unicode(8), nullable=False)
    contact = db.Column(db.String(16), nullable=False)
    stu_num = db.Column(db.SmallInteger, nullable=False)
    description = db.Column(db.Unicode(256), nullable=False)
    canceled = db.Column(db.Boolean, nullable=False, default=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

    def booking_stu(self):
        return [rec.stu_id for rec in
                SBLink.query.filter_by(book_id=self.book_id)]

    def update_confirm(self):
        '''
        更新一个预约，即若全部确认，数据库标注confirmed

        由view部分检测不冲突后触发，并非用户确认后立马更新
        '''
        if all([rec.confirmed for rec in
                SBLink.query.filter_by(
                    book_id=self.book_id).all()]):
            self.confirmed = True
            db.session.add(self)
            db.session.commit()
            return True
        return False

    def cancel(self):
        '''
        取消一个预约，即数据库标注canceled
        '''
        self.canceled = True
        db.session.add(self)
        db.session.commit()

    def get_confirm_status(self):
        return [{'studentId': rec.stu_id,
                 'rawStudentId': rec.raw_stu_id,
                 'confirmed': rec.confirmed}
                for rec in SBLink.query.filter_by(book_id=self.book_id).all()]

    @classmethod
    def commit_booking(cls, stu_ids: list,
                       room_id: int,
                       date: datetime.date,
                       start: datetime.time,
                       end: datetime.time,
                       sponsor: str,
                       contact: str,
                       stu_num: int,
                       description: str,
                       ) -> int:
        '''
        保存一个合法的未确认预约。

        :start:, :end: 精确到分
        '''
        book_rec = cls(room_id=room_id,
                       date=date, start_time=start,
                       end_time=end, sponsor=sponsor,
                       contact=contact, stu_num=stu_num,
                       description=description)
        db.session.add(book_rec)
        db.session.commit()
        SBLink.mklink(book_rec.book_id, stu_ids)
        return book_rec.book_id

    @classmethod
    def get_booking_info(cls):
        '''
        获取预约时间内的已有的预约信息。

        注意要考虑已经取消的预约。
        |Today  0:00|1|2|3|4|5|6|7|8|
        |when book  | | |*|*|*|*|*| |
        |Today 24:00| | |*|*|*|*|*| |

        返回
        --------
        list of dict
        '''
        today = datetime.date.today()
        info = []

        for booking in cls.get_booking_between(
                CONFIG.API.BOOKING.DAY_NEAREST,
                CONFIG.API.BOOKING.DAY_FARTHEST
        ):
            datedelta = (booking.date - today).days
            # Parse time on the server side
            # Need better implementation according to future demand
            start = booking.start_time.hour
            end = booking.end_time.hour
            info.append({
                'day': datedelta,
                'roomId': booking.room_id,
                'start': start,
                'end': end,
            })

        return info

    @classmethod
    def get_booking_between(cls, start: int, end: int):
        '''
        获取今天开始start到end天的全院未取消且已确认预约信息。

        包括第start天和第end天。参见BookRec.get_booking_info
        '''
        today = datetime.date.today()
        return cls.query.filter(
            cls.date.between(
                today+datetime.timedelta(start),
                today+datetime.timedelta(end))
        ).filter_by(
            canceled=False,
            confirmed=True).all()

    @classmethod
    def get_by_room_date(cls, room_id, date: datetime.date):
        return cls.query.filter_by(
            date=date,
            room_id=room_id,
            canceled=False,
            confirmed=True).all()

    @classmethod
    def get_stu_booking(cls, stu_id):
        '''
        获取给定学生尚未过期的预约记录，已取消的预约也返回

        命名约定: get_booking 就指期限内的，get_all_booking就是全部
        用于提示预约情况，故返回当天到7天后的记录

        :return: list of BookRec
        '''
        today = datetime.date.today()
        q = BookRec.query.join(SBLink, BookRec.book_id == SBLink.book_id)
        q = q.filter(BookRec.date.between(
            today, today+datetime.timedelta(
                CONFIG.API.BOOKING.DAY_FARTHEST + 1)))
        return q.filter_by(stu_id=stu_id).all()

    @classmethod
    def get_stu_book_count_now(cls, stu_id):
        '''
        today   1   2   | 3  4  5  6  7 |
        -confrimed ones-|--all bookings--
        '''
        today = datetime.date.today()
        q = BookRec.query.join(SBLink, BookRec.book_id == SBLink.book_id)
        q = q.filter_by(stu_id=stu_id).filter(
                BookRec.canceled == False)  # NOQA
        count = q.filter(BookRec.confirmed == True,  # NOQA
                         BookRec.date.between(
                             today, today+datetime.timedelta(
                                 CONFIG.API.BOOKING.DAY_NEAREST-1))
                         ).count()
        count += q.filter(BookRec.date.between(
            today+datetime.timedelta(CONFIG.API.BOOKING.DAY_NEAREST),
            today+datetime.timedelta(CONFIG.API.BOOKING.DAY_FARTHEST + 1))
        ).count()
        # print(stu_id, count)
        return count

    @classmethod
    def get_stu_all_booking(cls, stu_id):
        '''
        获取给定学生全部的预约记录，已取消以及未确认的预约也返回

        命名约定: get_booking 就指期限内的，get_all_booking就是全部

        返回
        --------
        list of BookRec
        '''
        q = BookRec.query.join(SBLink, BookRec.book_id == SBLink.book_id)
        return q.filter_by(stu_id=stu_id).all()

    @classmethod
    def stu_confirm(cls, stu_id, book_id):
        rec = SBLink.query.filter_by(book_id=book_id,
                                     stu_id=stu_id).first()
        rec.confirmed = True
        db.session.add(rec)
        db.session.commit()


# Flask-SQLAlchemy docs says:
# If you want to use many-to-many relationships you will need to
# define a helper table that is used for the relationship.
# For this helper table it is strongly recommended to not use a model
# but an actual table.
#
# However, we need to store confirm status info and according to
# https://stackoverflow.com/questions/45044926/db-model-vs-db-table-in-flask-sqlalchemy
# https://stackoverflow.com/questions/7417906/sqlalchemy-manytomany-secondary-table-with-additional-fields
# In a word, if you don't need to store extra data about the relationship,
# just use db.Table, it will save your time.

# Double primary keys will not keep orders in the table to distinguish sponsor


class SBLink(db.Model):
    __tablename__ = 'SBLink'

    rec_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    stu_id = db.Column(db.String(32), nullable=False)
    raw_stu_id = db.Column(db.String(32), nullable=False)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def mklink(cls, book_id: int, stu_ids: list) -> None:
        '''建立预约id和学生之间的 many-to-many 链接记录'''
        for stu_id, raw_stu_id in stu_ids:
            db.session.add(cls(book_id=book_id,
                               stu_id=stu_id,
                               raw_stu_id=raw_stu_id))
        db.session.commit()
