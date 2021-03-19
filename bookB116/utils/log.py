'''
Logging Helpers

Any thing in `bookB116` should not be imported in module level because
    this module is imported by `logging` to set up logger,
    which is done in the `setting` process
'''

import logging
from logging.handlers import SMTPHandler

from flask import has_request_context, request


class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.student = record.request = ''
        if has_request_context():
            record.request = '(%s %s by %s)' % (request.method, request.url,
                                                request.remote_addr)
            record.student = request.args.get('id', 'Anonymous')
        return super().format(record)


class SSLSMTPHandler(SMTPHandler):
    def emit(self, record):
        from bookB116.email import send_email

        send_email(','.join(self.toaddrs), self.subject,
                   self.format(record), mime='plain',
                   fromaddr=self.fromaddr)
