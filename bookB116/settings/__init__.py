import datetime
import os.path
from os import environ
from logging import getLogger
from logging.config import dictConfig

import yaml
from box import Box


PROJECT_ROOT = os.path.split(__file__)[0]
VALID_ENVS = ['production', 'development', 'testing']

FLASK_ENV = environ.get('FLASK_ENV') or 'production'
if FLASK_ENV not in VALID_ENVS:
    raise ValueError('FLASK_ENV invalid')


def config_file(config_name: str) -> str:
    return os.path.join(PROJECT_ROOT, config_name + '.yaml')


class Interval:
    '''Helper to add interval with datetime.time'''
    def __init__(self, minutes):
        self.minutes = minutes

    def __radd__(self, value):
        if isinstance(value, datetime.time):
            dt = datetime.datetime.combine(datetime.date.today(), value) +\
                    datetime.timedelta(minutes=self.minutes)
            return dt.time()
        raise NotImplementedError

    def __rsub__(self, value):
        if isinstance(value, datetime.time):
            dt = datetime.datetime.combine(datetime.date.today(), value) -\
                    datetime.timedelta(minutes=self.minutes)
            return dt.time()
        raise NotImplementedError


def time_constructor(loader, node):
    value = loader.construct_scalar(node)
    return datetime.datetime.strptime(value, '%H:%M').time()


# That's confusing when you copied and pasted code from StackOverflow,
# only to find that could not determine a constructor.
# That's because the default Parameter for Loader is yaml.Loader,
# but PyYAML suggested you to use safe_load...
yaml.add_constructor('!time', time_constructor, Loader=yaml.SafeLoader)

with open(config_file('common'), encoding='utf8') as f:
    CONFIG = Box(yaml.safe_load(f))
with open(config_file(FLASK_ENV), encoding='utf8') as f:
    CONFIG.merge_update(Box(yaml.safe_load(f)))

# Load secrect config a.k.a. local config for flask config
if os.path.isfile(config_file('local')):  # pragma: no cover
    with open(config_file('local'), encoding='utf8') as f:
        local_config = Box(yaml.safe_load(f), default_box=True)
        CONFIG.merge_update(local_config.common)
        CONFIG.merge_update(local_config[FLASK_ENV])


CONFIG.API.BOOKING.INTERVAL = Interval(CONFIG.API.BOOKING.INTERVAL)
CONFIG.API.BOOKING.LONGEST = Interval(CONFIG.API.BOOKING.LONGEST)
if 'email' in CONFIG.LOGGING.handlers:
    CONFIG.LOGGING.handlers.email.mailhost = CONFIG.EMAIL.MAILHOST
    CONFIG.LOGGING.handlers.email.credentials = CONFIG.EMAIL.CREDENTIALS

# Filtering unused handler because
# `logging` will config them even unused
CONFIG.LOGGING.handlers = {
    handler_name: handler
    for handler_name, handler in CONFIG.LOGGING.handlers.items()
    if handler_name in CONFIG.LOGGING.root.handlers
}
dictConfig(CONFIG.LOGGING)

logger = getLogger(__name__)
logger.debug('All settings are loaded successfully:\n'
             '      Env: %s\n'
             '      Flask Settings: %s\n'
             '      Booking Settings: %s\n'
             '      Email Settings: %s\n'
             '      Logging Settings: %s',
             FLASK_ENV, CONFIG.FLASK, CONFIG.API.BOOKING,
             CONFIG.EMAIL, CONFIG.LOGGING)
