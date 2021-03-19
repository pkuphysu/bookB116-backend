from datetime import date, time, timedelta

import pytest

from bookB116 import create_app, cryptor, db
from bookB116.database import Student
from bookB116.api.booking.database import BookRec

from . import BOOK_IDS, RAW_STU_IDS, STU_IDS, STU_TOKENS, login


@pytest.fixture(scope='class')
def app():
    app = create_app()
    app.app_context().push()
    if not STU_IDS:
        STU_IDS.extend([cryptor.hashit(i) for i in RAW_STU_IDS])
    db.create_all()
    try:
        for stu_id in STU_IDS:
            db.session.add(Student(stu_id=stu_id))
        db.session.commit()
    except Exception as e:
        db.session.close()
        db.drop_all()
        raise e

    yield app
    db.session.close()
    db.drop_all()


@pytest.fixture(scope='class')
def client(app, request):
    client = app.test_client()
    if request.cls is not None:
        request.cls.client = client
    if not STU_TOKENS:
        STU_TOKENS.extend([login(client, i) for i in RAW_STU_IDS])
    print(STU_TOKENS)
    yield client
    client.set_cookie('token', '')


# @pytest.fixture(autouse=True)
# def assert_clear_session(client):
#     '''
#     Auto apply this fixture to assure clear session
#     Since sharing client fixture in class lead to less check

#     https://stackoverflow.com/a/22638709/8810271
#     '''
#     yield
#     with client.session_transaction() as sess:
#         assert 'stu_id' not in sess
#         assert 'vercode' not in sess


@pytest.fixture(scope='class')
def client_book(client):
    #            stu_ids room day  start      end
    create_book((1, 3, 0), 0,  3, (8,  0), (9,  50))
    create_book((2, 3, 1), 0,  3, (11, 0), (12, 50))
    create_book((2, 4, 6), 1, -3, (8,  0), (9,  50))
    create_book((5, 6, 2), 2,  3, (8,  0), (9,  50))
    create_book((5, 4, 6), 1,  1, (8,  0), (9,  50))
    for i in BOOK_IDS:
        book_rec = BookRec.query.get(i)
        for s in book_rec.booking_stu():
            BookRec.stu_confirm(s, i)
        book_rec.update_confirm()
    yield client


def create_book(id_indices, room_id, day_delta, start, end):
    stu_ids = []
    for i in id_indices:
        stu_ids.append((STU_IDS[i], RAW_STU_IDS[i]))
    BOOK_IDS.append(BookRec.commit_booking(
        stu_ids, room_id, date.today()+timedelta(day_delta),
        time(*start), time(*end), ' ', ' ', 3, '😀😀😀'))
