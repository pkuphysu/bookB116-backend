import pytest

from bookB116.api.booking.database import BookRec

from .. import RAW_STU_IDS, STU_IDS
from . import BookingClient


@pytest.mark.usefixtures('client')
class TestBookingProcess(BookingClient):
    '''
    Test all booking process, simulating the browser
    '''
    client = None

    def test_2_post(self):
        # post 2 books for confirm conflict use
        for i, j, k in ((2, 1, 3), (1, 0, 4)):
            rv = self.book((RAW_STU_IDS[j], RAW_STU_IDS[k]), user_index=i)
            assert rv.status_code == 200
            rv = self.login_get('/api/booking/my', user_index=i)
            assert rv.status_code == 200
            assert rv.json['bookCount']

    def test_confirm_conflict(self):
        for stu_id in (0, 4):
            rv = self.confirm(2, stu_id)
            assert rv.status_code == 200
        assert BookRec.query.get(2).confirmed
        rv = self.confirm(book_id=1, user_index=1)
        assert rv.status_code == 409

    def test_book_cancel(self):
        my_booking = BookRec.get_stu_booking(STU_IDS[1])
        assert len(my_booking) == 2
        book_id = my_booking[1].book_id
        rv = self.cancel(book_id, user_index=1)
        assert rv.status_code == 200

    def test_book_check(self):
        form = self.correct_book_form((RAW_STU_IDS[5], RAW_STU_IDS[3]),
                                      test=True)
        rv = self.login_post('/api/booking/book', json=form,
                             raw_required=True)
        assert rv.status_code == 200
        rv = self.login_get('/api/booking/my', user_index=5)
        assert rv.status_code == 200
        assert rv.json['bookCount'] == 0
