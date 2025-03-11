import http.server
import json
import logging
import os
import random
import requests
import time
import threading

lock = threading.Lock()

CONTENT_TYPE = 'application/json'
INTROSPECT_URL = os.environ.get('INTROSPECT_URL')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LOGGER = logging.getLogger(__name__)

class BaseHTTPHandler(http.server.BaseHTTPRequestHandler):
    pass

class DummyHandler(BaseHTTPHandler):

    _stats = {}
    _history = []

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', CONTENT_TYPE)
        self.end_headers()

        if self.path == '/stats':
            self.wfile.write(json.dumps(self._getStats()).encode('UTF-8'))
        elif self.path == '/history':
            self.wfile.write(json.dumps(self._getHistory()).encode('UTF-8'))
        elif self.path == '/clear':
            self._clear()

    def _clear(self):
        DummyHandler._stats = {}
        DummyHandler._history = []

    def _getStats(self):
        return DummyHandler._stats

    def _getHistory(self):
        return DummyHandler._history

class HTTPHandler(BaseHTTPHandler):

    credentials = ''

    def do_GET(self):
        response_status_code = 200
        send_extra_header = False

        if self.path == '/fail':
            response_status_code = self._generateRandomCode()
        elif self.path == '/delayed':
            time.sleep(self._generateDelay())
            response_status_code = 500
        elif ( len(HTTPHandler.credentials) > 0 ):
            if self._checkAuth():
                response_status_code = 200
            else:
                response_status_code = 401
                send_extra_header = True
        else:
            response_status_code = 200

        self.send_response(response_status_code)
        if send_extra_header:
            self.send_header('WWW-Authenticate', 'Test')
        self.send_header('Content-type', CONTENT_TYPE)
        self.end_headers()

        self._record(response_status_code=response_status_code)

    def do_POST(self):
        body = ''
        response_status_code = 200

        if self.path == '/fail':
            response_status_code = self._generateRandomCode()
        elif self.path == '/delayed':
            time.sleep(self._generateDelay())
            response_status_code = 500
        elif ( len(HTTPHandler.credentials) > 0 and not self._checkAuth() ):
            response_status_code = 401
            self.send_header('WWW-Authenticate', 'Test')
        else:
            # try:
                if 'content-length' in self.headers:
                    length = int(self.headers['content-length'])
                    body = str(self.rfile.read(length), "utf-8") if length > 0 else ''
                # json.loads(body)
                response_status_code = 200
            # except:
            #     response_status_code = 400

        self.send_response(response_status_code)
        self.send_header('Content-type', CONTENT_TYPE)
        self.end_headers()

        self._record(body=body, response_status_code=response_status_code)

    def _record(self, body='', response_status_code=''):
        with lock:

            if self.path not in DummyHandler._stats:
                DummyHandler._stats[self.path] = 0

            DummyHandler._stats[self.path] += 1

            DummyHandler._history.append({
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
                'requestline': self.requestline,
                'body': body,
                'response_status_code': response_status_code,
                'client_address': self.client_address[0],
                'client_port': self.client_address[1],
                'request_version': self.request_version,
                'verb': self.command,
                'path': self.path,
                'headers': [{h: self.headers[h]} for h in self.headers ]
            })

    def _generateRandomCode(self):
        return random.choice(list(range(402, 418))+list(range(500, 505)))

    def _generateDelay(self):
        return float(random.choice(range(1000, 10000))) / 1000

    def _checkAuth(self):
        try:
            credentials = self.headers['Authorization']
            expected = 'Basic ' + HTTPHandler.credentials.decode('UTF')
            if credentials.startswith('Bearer '):
                LOGGER.info("Got Bearer auth: {}".format(credentials))
                return self._introspect(credentials[7:])
            else:
                LOGGER.info("Matching {} with {}".format(credentials, expected))
                return credentials == expected
        except:
            LOGGER.info("No Authorization header present")
            return False

    def _introspect(self, token_string):
        LOGGER.info("Introspect token: {}".format(token_string))
        data = {'token' : token_string, 'token_type_hint' : 'access_token'}
        auth = ("dummyUser", "dummyPass")
        resp = requests.post(INTROSPECT_URL, data=data, auth=auth, verify=False)

        LOGGER.info("Introspect status_code: {}, response: {}".format(resp.status_code, resp.json()))

        return resp.status_code == 200 and resp.json().get('active') == True
