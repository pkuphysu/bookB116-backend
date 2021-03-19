from flask import Flask


def test_build_success(app: Flask):
    '''
    Test if we have built database
    successfully from the data file.
    We don't use fixture app because it
    will come with some testing data.
    '''
    # invoke the command directly
    result = app.test_cli_runner().invoke(
        args=['student', 'build', 'tests/test_data.csv'])
    assert 'Successfully built' in result.output


def test_send_summary(app: Flask):
    '''
    A weak test, just make sure no error occur
    '''
    result = app.test_cli_runner().invoke(args=['booking', 'send-summary'])
    assert 'Successfully sent' in result.output
    assert 'Successfully cleared' in result.output


class TestBookByHand:
    def test_success(self, app: Flask):
        from datetime import date, timedelta

        from . import RAW_STU_IDS
        from bookB116.api.booking.database import BookRec

        command = (
            f'booking book -i {RAW_STU_IDS[1]} -r 0'
            f' -d {date.today()+timedelta(days=10)}'
            ' -s 10:00 -e 12:50 -p Lala -c 11411411411 -n 3 -de hahaha'
        )
        result = app.test_cli_runner().invoke(args=command.split())
        assert 'Book success' in result.output
        record = BookRec.query.first()
        assert record is not None
        assert record.sponsor == 'Lala'
        assert BookRec.get_booking_between(9, 11)

    def test_fail(self, app: Flask):
        command = (
            'booking book -i 1912345678 -r 0 -d 2020-10-10 -s 10:00'
            ' -e 12:50 -p TTH -c 11411411411 -n 3 -de hahaha'
        )
        result = app.test_cli_runner().invoke(args=command.split())
        assert 'typo' in result.output
