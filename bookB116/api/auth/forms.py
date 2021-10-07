from wtforms import StringField

from bookB116.utils.validation import AbortForm, AuthStu


class AuthForm(AbortForm):
    queryString = StringField(validators=[AuthStu()])
