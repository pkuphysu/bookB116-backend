from base64 import urlsafe_b64encode, urlsafe_b64decode
from logging import getLogger

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

logger = getLogger(__name__)


class Cryptor:
    def __init__(self):
        self.key = None

    def init_app(self, app):
        self.key = app.config.get('FERNET_KEY', None).encode('ascii')
        self.EXPIRE = app.config.get('VERCODE_EXPIRE', 60)
        self.SCRYPT_LEVEL = app.config.get('SCRYPT_LEVEL', 14)

        self.fernet = Fernet(self.key)
        self.hmac = hmac.HMAC(
            self.key, hashes.SHA256(), backend=default_backend())

    @property
    def kdf(self):
        # https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/#scrypt
        return Scrypt(
            salt=self.key, backend=default_backend(),
            length=32, n=2**self.SCRYPT_LEVEL, r=8, p=1
        )

    def hashit(self, s: str) -> str:
        key = self.kdf.derive(s.encode('utf-8'))
        return urlsafe_b64encode(key[:18]).decode('ascii')

    def _digest_hmac(self, s):
        h = self.hmac.copy()
        for i in s:
            h.update(i.encode('utf-8'))
        return h

    def generate_hmac(self, data):
        h = self._digest_hmac(data)
        return urlsafe_b64encode(h.finalize()).decode('ascii')

    def verify_hmac(self, data, signature):
        h = self._digest_hmac(data)
        try:
            h.verify(urlsafe_b64decode(signature.encode('ascii')))
            return True
        except:  # noqa
            return False

    def generate_user_token(self, stu_id: str, timestamp: str) -> str:
        return self.generate_hmac((stu_id, timestamp))

    def verify_user_token(self, stu_id: str, timestamp: str,
                          signature: str) -> bool:
        return self.verify_hmac((stu_id, timestamp), signature)

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(value.encode('ascii')).decode('ascii')

    def decrypt(self, token: bytes) -> str:
        return self.fernet.decrypt(token, self.EXPIRE).decode('ascii')

    def equal(self, value: str, token: str) -> bool:
        '''
        测试是否相等且时间间隔符合要求

        参数
        --------
        value: str, 测试的字符串
        token: bytes, 测试的密码

        返回
        --------
        True/False
        '''
        if not token or not value:
            logger.info('Deny empty token or value')
            return False
        token = token.encode('ascii')
        try:
            if value == self.decrypt(token):
                return True
            else:
                logger.info('Deny %s for not literally equal', value)
        except InvalidToken:
            logger.info('Deny %s for token is invalid', value)

        return False
