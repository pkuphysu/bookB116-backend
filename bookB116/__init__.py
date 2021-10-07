from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from oic.oic import Client
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oic.message import RegistrationResponse, ProviderConfigurationResponse

from bookB116.settings import CONFIG
from bookB116.utils.crypt import Cryptor
from bookB116.utils.session import Session

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cryptor = Cryptor()
client = Client(client_authn_method=CLIENT_AUTHN_METHOD)
op_info = ProviderConfigurationResponse(
    version="1.0", issuer=CONFIG.OPENIDAUTH.ISSUER,
    authorization_endpoint=CONFIG.OPENIDAUTH.AUTHORIZATION_ENDPOINT,
    token_endpoint=CONFIG.OPENIDAUTH.TOKEN_ENDPOINT,
    userinfo_endpoint=CONFIG.OPENIDAUTH.USERINFO_ENDPOINT,
    end_session_endpoint=CONFIG.OPENIDAUTH.END_SESSION_ENDPOINT,
    introspection_endpoint=CONFIG.OPENIDAUTH.INTROSPECTION_ENDPOINT,
    jwks_uri=CONFIG.OPENIDAUTH.JWKS_URI
)
info = {
    "client_id": CONFIG.OPENIDAUTH.CLIENT_ID,
    "client_secret": CONFIG.OPENIDAUTH.CLIENT_SECRET,
    "redirect_uris": CONFIG.OPENIDAUTH.REDIRECT_URIS,
    "scope": CONFIG.OPENIDAUTH.SCOPE
}
client_reg = RegistrationResponse(**info)
print(client_reg["client_id"])
client.handle_provider_config(op_info, op_info['issuer'])
client.store_registration_info(client_reg)


class PrefixMiddleware(object):

    def __init__(self, app, prefix=CONFIG.FLASK.PATH_PREFIX):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]


def create_app():
    '''
    创建一个Flask app实例。
    settings 已将测试环境考虑，倒入即可
    '''
    app = Flask(__name__)
    app.config.update(CONFIG.FLASK)
    app.wsgi_app = PrefixMiddleware(app.wsgi_app)

    db.init_app(app)
    migrate.init_app(app, db)
    cryptor.init_app(app)

    if app.env == 'development':
        CORS(
            app, origins=r'http://localhost:.\d*',
            supports_credentials=True
        )

    app.config['SESSION_SQLALCHEMY'] = db
    Session(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from . import api, cli

    api.init_app(app)
    cli.init_app(app)

    app.errorhandler(HTTPException)(handle_exception)

    app.logger.info('Successfully start app')
    return app


def handle_exception(e):
    print(e.code, e.description)
    return jsonify(code=e.code, message=e.description), e.code
