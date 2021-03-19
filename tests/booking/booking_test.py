from datetime import date, datetime, time, timedelta

import pytest

from bookB116.api.booking.database import BookRec

from .. import BOOK_IDS, RAW_STU_IDS, STU_IDS
from . import BookingClient

TODAY = datetime.combine(date.today(), time(0, 0))
START = int((TODAY+timedelta(5, hours=9)).timestamp())
END = int((TODAY+timedelta(5, hours=10, minutes=50)).timestamp())


def test_book_db(client_book):
    # assert len(BookRec.get_booking_info()[3]) == 3
    his_book_info = BookRec.get_stu_booking(STU_IDS[2])
    assert len(his_book_info) == 2
    book_to_cancel = his_book_info[0]
    book_to_cancel.cancel()
    assert book_to_cancel.canceled
    # assert len(BookRec.get_booking_info()[3]) == 2
    assert len(BookRec.get_stu_all_booking(STU_IDS[2])) == 3


@pytest.mark.usefixtures('client_book')
class TestInvalidBook(BookingClient):
    def test_book_invalid_room(self):
        rv = self.book((RAW_STU_IDS[0], RAW_STU_IDS[4]), room_id=8,
                       user_index=7)
        assert rv.status_code == 400

    @pytest.mark.skip(reason='1 student booking enabled now')
    @pytest.mark.parametrize('data', [('1912332133', RAW_STU_IDS[4]),
                                      (RAW_STU_IDS[4], RAW_STU_IDS[7]),
                                      (RAW_STU_IDS[4], RAW_STU_IDS[4])])
    def test_invalid_invitation(self, data):
        assert self.book(data, user_index=7).status_code == 400

    def test_book_invalid_time(self):
        start = int((TODAY+timedelta(3, hours=7)).timestamp())
        rv = self.book(
            (RAW_STU_IDS[0], RAW_STU_IDS[4]), room_id=2, start=start,
            user_index=7)
        assert rv.status_code == 400

    def test_invitee_exceed(self):
        rv = self.book((RAW_STU_IDS[1], RAW_STU_IDS[3]), user_index=7)
        assert rv.status_code == 400
        assert b'Invitee Exceed' in rv.data

    def test_sponsor_exceed(self):
        rv = self.book((RAW_STU_IDS[4], RAW_STU_IDS[0]), user_index=2)
        assert rv.status_code == 409
        assert b'Sponsor Exceed' in rv.data

    def test_book_vercode_invalid(self):
        _, rv = self.get_twice_vercode(user_index=7)
        assert rv.status_code == 200
        rv = self.login_post('/api/booking/book', json={
            'start': 1234567890,
            'end': 1234567890,
            'room_id': 1,
            'stu1': 1234567,
            'stu2': 1234567,
            'vercode': 'sdfg'
        }, user_index=7)
        assert rv.status_code == 400
        assert b'Code Error' in rv.data


@pytest.mark.usefixtures('client_book')
class TestInvalidCancel(BookingClient):
    def test_not_exist(self):
        assert self.cancel(129078543).status_code == 404

    def test_others(self):
        assert self.cancel(BOOK_IDS[0]).status_code == 404

    def test_no_previlege(self):
        assert self.cancel(BOOK_IDS[3]).status_code == 403

    def test_canceled(self):
        assert self.cancel(BOOK_IDS[1]).status_code == 200
        assert self.cancel(BOOK_IDS[1]).status_code == 403

    def test_expired(self):
        assert self.cancel(BOOK_IDS[2]).status_code == 403


'''
@pytest.mark.parametrize('vercode', ['0123'])
def test_not_get_vercode(client, vercode):
    login(client, RAW_STU_IDS[2])
    rv = client.post('/api/booking/book', data={
        'start': 1234567890,
        'end': 1234567890,
        'room_id': 1,
        'stu1': 1234567,
        'stu2': 1234567,
        'vercode': vercode
    },
        follow_redirects=True)
    assert rv.status_code == 400
    assert b'code first' in rv.data


@pytest.mark.parametrize('data', [
    {
        'start': 1234567890,
        'end': 1234567890,
    },
    {
        'start': 1234567890,
        'end': 1234567890,
        'room_id': 1,
        'stu1': 1234567,
        'stu2': 1234567,
        'vercode': 1234},
    {}
])
def test_book_form_invalid(client, data):
    login(client, RAW_STU_IDS[2])
    rv = client.post('/api/booking/book', data=data,
                     follow_redirects=True)
    assert rv.status_code == 400
    assert b'code first' in rv.data or b'require' in rv.data


def test_cancel_not_get_vercode(client):
    login(client, RAW_STU_IDS[2])
    rv = client.post('/api/booking/cancel', data={
        'book_id': 129078543,
        'vercode': '1234'
    }, follow_redirects=True)
    assert rv.status_code == 400
    assert b'code first' in rv.data


@pytest.mark.parametrize('vercode', ['dhhj', 1123, '2123'])
def test_cancel_vercode_invalid(client, vercode):
    login(client, RAW_STU_IDS[2])
    rv = request_twice_vercode(client)
    assert b'OK' == rv.data
    rv = client.post('/api/booking/cancel', data={
        'book_id': 129078543,
        'vercode': vercode
    }, follow_redirects=True)
    assert rv.status_code == 400
    assert b'Code Error' in rv.data


@pytest.mark.parametrize('data', [{'book_id': 129078543},
                                  {'vercode': 1234, 'book_id': 129078543},
                                  {}])
def test_cancel_form_invalid(client, data):
    login(client, RAW_STU_IDS[2])
    rv = client.post('/api/booking/cancel', data=data,
                     follow_redirects=True)
    assert rv.status_code == 400
    if 'book_id' not in data:
        assert b'require' in rv.data
    else:
        assert b'code first' in rv.data
'''
