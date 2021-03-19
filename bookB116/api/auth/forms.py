from wtforms import StringField

from bookB116.utils.validation import AbortForm, Vercode, RequireStu


class LoginForm(AbortForm):
    vercode = StringField(validators=[Vercode()])


class VercodeForm(AbortForm):
    stu_id = StringField(validators=[RequireStu()])
