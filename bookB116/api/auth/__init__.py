from flask import Blueprint

from .utils import get_send_vercode


bp = Blueprint('auth', __name__)

from . import routes  # noqa

__all__ = ['get_send_vercode']
