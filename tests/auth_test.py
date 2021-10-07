from time import sleep

import pytest

from . import Client, RAW_STU_IDS, login
from .booking import BookingClient


@pytest.mark.usefixtures('client')
class TestAuthWorking(Client):
    def test_authorize(self):
        # rv = self.client.get('/api/booking/all')
        # assert rv.status_code == 403

        rv = self.login_get('/api/booking/all')
        assert rv.status_code == 200


# @pytest.mark.usefixtures('client')
# class TestAuthInvalidAction(Client):
    # @pytest.mark.skip(reason='using same vercode for testing now')
    # def test_twice_ver_and_login(self):
    #     vercode, _ = self.get_twice_vercode()
    #     self.get_vercode(json={'stu_id': RAW_STU_IDS[4]})
    #     rv = self.client.post('/api/login', json={'vercode': vercode})
    #     assert b'Code Error' in rv.data

    # def test_modify_vercode(self):
    #     '''Though it is impossible to modify a signed session'''
    #     self.get_vercode()
    #     with self.client.session_transaction() as sess:
    #         sess['vercode'] = 'ajhdsjgauy35y463489y'
    #     rv = self.client.post('/api/login', json={'vercode': '2344'})
    #     assert b'Code Error' in rv.data

    # def test_not_get_vercode(self):
    #     rv = self.client.post('/api/login', json={'vercode': '1234'},
    #                           follow_redirects=True)
    #     assert b'First' in rv.data

    # def test_vercode_invalid(self):
    #     _, rv = self.get_vercode(json={'stu_id': RAW_STU_IDS[4]})
    #     assert rv.status_code == 200
    #     rv = self.client.post('/api/login', json={'vercode': '1234'})
    #     assert b'Code Error' in rv.data


# @pytest.mark.usefixtures('client')
# class TestAuthWrongFormat(Client):
#     client = None

#     @pytest.mark.parametrize(
#         'json',
#         [None, {},
#          {'nothing': ''},
#          {'stu_id': {'sth': 123}},
#          {'stu_id': ''},
#          {'stu_id': None}])
#     def test_getvercode(self, json):
#         # Here the server do not generate vercode
#         # so there is no need to use get_vercode
#         # to pop a vercode
#         rv = self.client.post('/api/vercode', json=json)
#         assert rv.status_code == 400

#     @pytest.mark.parametrize(
#         'json', [None, {},
#                  {'nothing': ''},
#                  {'vercode': '1234'},
#                  {'vercode': 1234},
#                  {'vercode': 'adg'},
#                  {'vercode': ''},
#                  {'vercode': {'sth': 123}}])
#     def test_login(self, json):
#         _, rv = self.get_vercode(json={'stu_id': RAW_STU_IDS[0]})
#         rv = self.client.post('/api/login', json=json)
#         assert b'Code Error' in rv.data


@pytest.mark.usefixtures('client')
class TestBadBookAuth(BookingClient):
    def test_vercode_not_mine(self):
        victim = login(self.client, RAW_STU_IDS[0])
        form = self.correct_book_form((RAW_STU_IDS[5], RAW_STU_IDS[3]),
                                      user_index=2)
        rv = self.client.post(
            (f"/api/booking/book?id={victim['id']}&rawId={RAW_STU_IDS[3]}"
             f"&timestamp={victim['timestamp']}"),
            json=form)
        assert rv.status_code == 403


# class TestLogout(Client):
#     def test_logout(self, client):
#         self.login_get('/api/booking/my')
#         sleep(1)
#         self.login_get('/api/logout')
#         rv = self.login_get('/api/booking/my')
#         assert rv.status_code == 403
