from os import environ
import sys

# Must set environ first
environ['FLASK_ENV'] = 'testing'


RAW_STU_IDS = ['2000000000', '2000000001', '2000000002', '2000000003',
               '2000000004', '2000000005', '2000000006', '2000000007']
STU_IDS = []
STU_TOKENS = []
BOOK_IDS = []


class WebSocket:
    send = print

    def connect(self, *args, **kargs):
        print(args, kargs)


websocket = type(sys)('websocket')
websocket.WebSocket = WebSocket
sys.modules['websocket'] = websocket


def login(client, stu_id):
    rv = client.post('/api/auth', json={'queryString': 'qs'})
    assert rv.status_code == 200
    print(rv)
    return rv.json['user']


class Client:
    client = None
    current_user = None

    def _login_open(self, method, path, json=None,
                    user_index=0, raw_required=False):
        print('current:', self.current_user)
        if self.current_user and self.current_user['index'] == user_index:
            u = self.current_user
        else:
            u = login(self.client, RAW_STU_IDS[user_index])
            u['index'] = user_index
            self.current_user = u
        query = f"?id={u['id']}&timestamp={u['timestamp']}"
        if raw_required:
            query += f"&rawId={u['rawId']}"
        # self.client.set_cookie('token', u['token'])
        return self.client.open(path + query, method=method, json=json)

    def login_post(self, *args, **kargs):
        return self._login_open('POST', *args, **kargs)

    def login_get(self, *args, **kargs):
        return self._login_open('GET', *args, **kargs)

    def get_vercode(self, user_index=0):
        rv = self.login_get(
            '/api/vercode',
            user_index=user_index,
            raw_required=True)
        assert rv.status_code == 200
        return '1000', rv

    # def get_vercode(self, json):
    #     rv = self.client.post('/api/vercode', json=json)
    #     return '1000', rv
