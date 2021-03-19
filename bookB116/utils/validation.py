from urllib.parse import urljoin, urlparse
from logging import getLogger

from flask import request, session, abort, flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, ValidationError, StopValidation

from bookB116.database import Student
from bookB116 import cryptor


logger = getLogger(__name__)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


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


class Vercode(object):
    def __call__(self, form, field):
        token = session.pop('vercode', '')
        if not token:
            raise ValidationError('Get Code First')
        if not cryptor.equal(value=field.data,
                             token=token):
            raise ValidationError('Verification Code Error')
