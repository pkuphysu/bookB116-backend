from importlib import import_module
from functools import wraps

import os
from logging import getLogger

from flask import Flask


logger = getLogger(__name__)
modules = ['student', 'database']
development = os.environ.get('FLASK_ENV') == 'development'


def dev_help_prod_error(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        from bookB116 import db
        from mysql.connector.errors import ProgrammingError

        if development:
            db.create_all()
        try:
            f(*args, **kwargs)
        except ProgrammingError as e:
            if not development and 'doesn\'t exist' in e.msg:
                logger.error('Please create database via migrate')
            else:
                raise e from None
    return wrap


def init_app(app: Flask) -> None:
    for module in modules:
        app.cli.add_command(import_module(
            '.' + module, package='bookB116.cli').cli)
