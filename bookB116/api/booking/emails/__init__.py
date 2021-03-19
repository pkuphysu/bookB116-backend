from datetime import date, timedelta


from bookB116.email import send_email, get_template
from bookB116.settings import CONFIG


tomorrow = date.today()+timedelta(1)


def send_summary(all_booking):
    data_week = {tomorrow+timedelta(d):
                 [book_rec for book_rec in all_booking
                  if book_rec.date == tomorrow+timedelta(d)]
                 for d in range(1, CONFIG.API.BOOKING.DAY_FARTHEST)}
    data_tomorrow = [book_rec for book_rec in all_booking
                     if book_rec.date == tomorrow]

    tmpl = get_template(__file__, 'summary.html')
    msg = tmpl.render(tomorrow=tomorrow,
                      today=tomorrow-timedelta(1),
                      data_tomorrow=data_tomorrow,
                      data_week=data_week,
                      rooms=CONFIG.API.BOOKING.B116ROOMS)
    print(msg)
    receiver = CONFIG.API.BOOKING.SUMMARY.RECEIVERS
    send_email(receiver, CONFIG.API.BOOKING.SUMMARY.TITLE, msg)
    # with open('mail_eg/summary.html', 'w', encoding='utf-8') as f:
    #     f.write(msg)
