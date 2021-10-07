from urllib.parse import urljoin, urlparse
from logging import getLogger
import requests
from bookB116.settings import CONFIG

from flask import request, session, abort, flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, ValidationError, StopValidation
from oic.oic.message import AuthorizationResponse

from bookB116.database import Student
from bookB116 import cryptor, client


logger = getLogger(__name__)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def get_pkuid_from_auth(query_string: str):
    aresp = client.parse_response(AuthorizationResponse, info=query_string,
                                  sformat="urlencoded")
    state = aresp["state"]
    sessionState = session.pop('state', None)
    sessionNonce = session.pop('nonce', None)
    if sessionState is None:
        logger.info('Invalid auth without login /auth')
        raise ValidationError('Login First')
    if state != sessionState:
        logger.info(f'Invalid state \nstate in session:{sessionState}\n\
            state in request:{state}/auth')
        raise ValidationError('Auth Fail')
    try:
        resp = client.do_access_token_request(state=aresp["state"],
                                              request_args={
            "code": aresp["code"]},
            authn_method="client_secret_basic")
        assert resp['id_token']['nonce'] == sessionNonce, 'Invalid nonce'
        access_token = resp['access_token']
        res = requests.get(CONFIG.OPENIDAUTH.USERINFO_ENDPOINT,
                           headers={"Authorization": f"Bearer {access_token}"})
        # 不知道为什么，用oic的userinfo就请求不来。。。
        if res.status_code != 200:
            if res.status_code == 401:
                logger.info('Unauthorized /auth/UserInfo')
                raise ValidationError('Auth Fail')
            else:
                raise ValidationError(
                    f'UnknownError:res.status_code={res.status_code} \
                        /auth/UserInfo')
        raw_stu_id = res.json()['pku_id']
        assert raw_stu_id is not None
    except Exception as e:
        logger.info('ERROR:'+repr(e)+' /auth')
        raise ValidationError('Network Error')
    return raw_stu_id


class AbortForm(FlaskForm):
    '''
    Simple override of the default behaviour

    AbortForm aborts the request with json error response
        when valitation fails
    '''

    def validate(self):
        if super().validate():
            valid, result = self.custom_validate()
            if valid:
                return result
            error_msg = result
        else:
            # using sum will cause int + list
            error_msg = [err for _ in
                         self.errors.values() for err in _]
        logger.info('Bad form: %s\n\t%s %s', self.data,
                    self.errors, error_msg)
        abort(400, error_msg)

    def custom_validate(self):
        '''
        Custom validate function on whole form
        Should return a tuple of (True, return_value) if valid
            and can return False and list of error msgs if invalid
            or you can just lazy abort
        '''
        return True, None


class FlashForm(FlaskForm):
    def validate(self):
        if super().validate() and self.custom_validate():
            return True
        logger.info('Bad form: %s\n\t%s', self.data,
                    self.errors)
        for errs in self.errors.values():
            for err in errs:
                flash(err)

    def custom_validate(self):
        return True


class OnlyIfNot(DataRequired):
    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super().__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' %
                            self.other_field_name)
        if bool(other_field.data):
            if bool(field.data):
                raise ValidationError('Both fields are non-empty.')
            raise StopValidation()
        else:
            super().__call__(form, field)


class RequireStu(DataRequired):
    def __call__(self, form, field):
        super().__call__(form, field)
        raw_stu_id = str(field.data)
        if len(raw_stu_id) == 10:
            if Student.by_raw_id(raw_stu_id):
                return True
        raise ValidationError('User Not Found')


class AuthStu(DataRequired):
    def __call__(self, form, field):
        super().__call__(form, field)
        query_string = str(field.data)
        if CONFIG.FLASK.TESTING:
            raw_stu_id = CONFIG.OPENIDAUTH.TESTING_ID
        else:
            raw_stu_id = get_pkuid_from_auth(query_string)
        user = Student.by_raw_id(raw_stu_id)
        if user is None:
            user = Student.add_raw_id(raw_stu_id)
        session['raw_stu_id'] = raw_stu_id
        return True


class Vercode(object):
    def __call__(self, form, field):
        token = session.pop('vercode', '')
        if not token:
            raise ValidationError('Get Code First')
        if not cryptor.equal(value=field.data,
                             token=token):
            raise ValidationError('Verification Code Error')
