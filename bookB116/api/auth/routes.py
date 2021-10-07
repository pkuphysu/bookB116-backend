from logging import getLogger
from time import time
import datetime
from bookB116.settings import CONFIG

import flask_login
from flask import abort, request, session, jsonify
from flask import current_app as app
from oic import rndstr

from bookB116 import cryptor, login_manager, client
from bookB116.database import Student

from . import bp
from .forms import AuthForm
from .utils import get_send_vercode

logger = getLogger(__name__)


@login_manager.request_loader
def request_loader(req):
    stu_id = req.args.get('id')
    timestamp = req.args.get('timestamp')
    token = req.cookies.get('token')
    if not (stu_id and token and timestamp):
        logger.warning('Mal-formed query %s', req.args)
        return
    if session.get('__id__') != stu_id:
        logger.warn('Use token with bad login %s', session.get('__id__'))
        return
    if not cryptor.verify_user_token(stu_id, timestamp, token):
        logger.warning('Bad token: %s', req.args)
        return
    student = Student.query.get(stu_id)
    if (student.full_logout_time and
            student.full_logout_time.timestamp() > int(timestamp)):
        logger.info('Login invalidated from %s to %s',
                    timestamp, student.full_logout_time.timestamp())
        return
    logger.debug('Log in %s', stu_id)
    return student


@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized_handler():
    """ Handle requests to login protected pages """
    abort(403, 'Unauthorized')


@bp.route("/api/login")
def login():
    '''
    session should be cleaned no matter what happens
    return a login_url to redirect

    state is used to keep track of responses to outstanding requests (state).
    nonce is a string value used to associate a Client session
    with an ID Token, and to mitigate replay attacks.
    '''
    session["state"] = rndstr()
    session["nonce"] = rndstr()
    args = {
        "client_id": client.client_id,
        "response_type": "code",
        "scope": CONFIG.OPENIDAUTH.SCOPE,
        "nonce": session["nonce"],
        "redirect_uri": CONFIG.OPENIDAUTH.REDIRECT_URIS[0],
        "state": session["state"]
    }
    auth_req = client.construct_AuthorizationRequest(request_args=args)
    login_url = auth_req.request(client.authorization_endpoint)
    return jsonify(message='Redirecting', url=login_url)


@bp.route('/api/auth', methods=["POST"])
def auth():
    auth_form = AuthForm()
    auth_form.validate()
    raw_stu_id = session.pop('raw_stu_id', None)
    if raw_stu_id is None:
        logger.info('Invalid login without requesting /get_vercode')
        abort(400, 'Login First')
    user = Student.by_raw_id(raw_stu_id)
    timestamp = str(int(time()))
    token = cryptor.generate_user_token(user.stu_id, timestamp)
    session['__id__'] = user.stu_id
    logger.info('Auth %s success', raw_stu_id)
    flask_login.login_user(user)

    response = jsonify(message='Logged In', user={
        'timestamp': timestamp,
        'rawId': raw_stu_id,
        'id': user.stu_id
    })
    response.set_cookie(
        'token', token, httponly=True,
        secure=app.config['SESSION_COOKIE_SECURE'],
        samesite=app.config['SESSION_COOKIE_SAMESITE'],
        expires=datetime.datetime.now() + datetime.timedelta(weeks=30)
    )
    return response


@bp.route('/api/logout')
@flask_login.login_required
def full_logout():
    flask_login.current_user.full_logout_at(time())
    logger.info('Fully logout %s', flask_login.current_user.stu_id)
    return jsonify(message='Logged out')


@bp.route('/api/vercode')
@flask_login.login_required
def vercode():
    '''send twice verification code to a login user via GET'''
    raw_stu_id = request.args.get('rawId')
    if not raw_stu_id or not cryptor.hashit(
            raw_stu_id) == request.args.get('id'):
        abort(403, 'Bad Authorization')
    session['vercode'] = cryptor.encrypt(get_send_vercode(raw_stu_id))
    return jsonify(message='Vercode Sent')
