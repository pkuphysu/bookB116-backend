import pytest

from smtplib import SMTPDataError

from . import Client, RAW_STU_IDS


# Not testing email send here because email not stable,
#     especially in CI env


# @pytest.mark.usefixtures('client')
# class TestMailError(Client):
#     def test_err_vercode(self):
#         from bookB116.api.auth import emails

#         def patch_mail_err(*_):
#             raise SMTPDataError(554, b'DT:SPM 163')

#         emails.send_email = patch_mail_err
#         _, rv = self.get_vercode()
#         print(rv)
#         # assert rv.status_code == 503
#         assert b'not sent' in rv.data

#         emails.send_email = print
