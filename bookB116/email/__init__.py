from bookB116.settings import CONFIG

from .core import send_email, get_template  # noqa


if CONFIG.FLASK.TESTING:
    send_email = print  # noqa
