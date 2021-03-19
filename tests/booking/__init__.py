from datetime import date, datetime, time, timedelta

from .. import Client

TODAY = datetime.combine(date.today(), time(0, 0))
START = int((TODAY+timedelta(5, hours=9)).timestamp())
END = int((TODAY+timedelta(5, hours=10, minutes=50)).timestamp())


class BookingClient(Client):
    def cancel(self, book_id, user_index=2):
        return self.login_post('/api/booking/cancel', json={
            'book_id': book_id,
            'vercode': self.get_twice_vercode(user_index)[0]
        }, user_index=user_index)

    def book(self, *args, user_index=2, **kargs):
        return self.login_post('/api/booking/book', user_index=user_index,
                               json=self.correct_book_form(
                                   *args, user_index=user_index, **kargs),
                               raw_required=True)

    def confirm(self, book_id, user_index=2):
        return self.login_post('/api/booking/confirm',
                               json={'book_id': book_id},
                               user_index=user_index)

    def correct_book_form(self, raw_stu_ids, *, room_id=0, user_index=2,
                          start=START, end=END, test=False):
        if test:
            vercode = ''
            test = True
        else:
            vercode = self.get_twice_vercode(user_index)[0]
            test = False

        return {
            'room_id': room_id,
            'start': start,
            'end': end,
            'stu1': raw_stu_ids[0],
            'stu2': raw_stu_ids[1],
            'vercode': vercode,
            'sponsor': 'phynoc',
            'contact': '12345678909',
            'description': 'pkuphynoc',
            'stu_num': 3,
            'test': test,
        }
