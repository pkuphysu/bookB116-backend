from logging import getLogger
from datetime import datetime

from bookB116 import cryptor, db

logger = getLogger(__name__)


class Student(db.Model):
    '''
    既是存储学生的数据库模板，又是用户登录管理的模板

    属性
    --------
    stu_id: 学生证件号码
    full_logout_time: 最后一次完全注销的时间
    wx_id: 微信id（相对本公众号的）
    '''
    __tablename__ = 'Students'

    stu_id = db.Column(db.String(32), primary_key=True)
    # Default of `full_logout_time` could be `sqlalchemy.sql.func.now`
    # But for easy testing, setting default to `None`
    full_logout_time = db.Column(db.DateTime, default=None)

    # It's starange that coverage does not track this
    # But deleting it will indeed cause error
    def is_active(self):
        """True, as all users are active."""
        return True   # pragma: no cover

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.stu_id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True   # pragma: no cover

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False  # pragma: no cover

    def full_logout_at(self, timestamp: int) -> None:
        self.full_logout_time = datetime.fromtimestamp(timestamp)
        db.session.commit()

    @classmethod
    def by_raw_id(cls, raw_student_id: str):
        return cls.query.get(cryptor.hashit(raw_student_id))

    @classmethod
    def add_raw_id(cls, raw_student_id: str):
        inserter = Student.__table__.insert().prefix_with('IGNORE')
        db.session.execute(inserter.values(
            stu_id=cryptor.hashit(raw_student_id)))
        db.session.commit()
        return cls.by_raw_id(raw_student_id)
