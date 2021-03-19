from datetime import date, time, timedelta

import pytest

from bookB116.api.booking.routes import is_valid_booking_time

TODAY = date.today()


@pytest.mark.usefixtures('client_book')
class TestWrongTime:
    '''
    In order to write easy and read easy,
        this test does not involve setting.BOOKING
    As a result, this test must change manually if policy changes

    (Though other test for booking needs change too,
        this needs to be changed most)
    '''
    client_book = None

    def test_earlier_than_nearest_day(self):
        assert not is_valid_booking_time(
            1, TODAY + timedelta(1), time(8, 0), time(9, 50))

    def test_later_than_book_day_farthest(self):
        assert not is_valid_booking_time(1, TODAY + timedelta(11),
                                         time(8, 0), time(9, 50))

    def test_start_later_than_end(self):
        assert not is_valid_booking_time(
            1, TODAY + timedelta(4), time(9, 0), time(8, 50))

    def test_just_in_early_working_hour(self):
        assert is_valid_booking_time(1, TODAY + timedelta(4),
                                     time(8, 0), time(8, 50))

    def test_just_in_late_working_hour(self):
        assert is_valid_booking_time(1, TODAY + timedelta(4),
                                     time(21, 0), time(21, 50))

    def test_not_in_the_working_hour(self):
        assert not is_valid_booking_time(1, TODAY + timedelta(4),
                                         time(21, 0), time(22, 50))

    def test_not_match_current_pattern(self):
        assert not is_valid_booking_time(1, TODAY + timedelta(4),
                                         time(16, 20), time(17, 50))
        assert not is_valid_booking_time(1, TODAY + timedelta(4),
                                         time(16, 0), time(17, 40))

    def test_time_too_long(self):
        assert not is_valid_booking_time(1, TODAY + timedelta(4),
                                         time(16, 0), time(20, 50))

    def test_time_span_just_right(self):
        assert is_valid_booking_time(
            1, TODAY + timedelta(4), time(17, 0), time(20, 50))

    def test_right_after_another_booking(self):
        assert not is_valid_booking_time(2, TODAY + timedelta(3),
                                         time(9, 0), time(10, 50))

    def test_conflict_with_another(self):
        assert not is_valid_booking_time(2, TODAY + timedelta(3),
                                         time(8, 0), time(9, 50))
        assert not is_valid_booking_time(2, TODAY + timedelta(3),
                                         time(8, 0), time(10, 50))
        assert not is_valid_booking_time(0, TODAY + timedelta(3),
                                         time(11, 00), time(11, 50))

    def test_dual_in_time_but_room_differ(self):
        assert is_valid_booking_time(
            1, TODAY + timedelta(3), time(9, 00), time(10, 50))

    def test_on_an_empty_day(self):
        assert is_valid_booking_time(
            2, TODAY + timedelta(7), time(9, 0), time(10, 50))

    def test_between_two_bookings(self):
        assert is_valid_booking_time(
            0, TODAY + timedelta(3), time(10, 0), time(10, 50))

    def test_days_in_the_edge(self):
        assert not is_valid_booking_time(0, TODAY + timedelta(2),
                                         time(9, 0), time(10, 50))
        assert not is_valid_booking_time(0, TODAY + timedelta(10),
                                         time(9, 0), time(10, 50))
