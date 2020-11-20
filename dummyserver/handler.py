import http.server
import json
import random
import time
import threading

lock = threading.Lock()

CONTENT_TYPE = 'application/json'

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
        if self.path == '/fail':
            self.send_response(self._generateRandomCode())
        elif self.path == '/delayed':
            time.sleep(self._generateDelay())
            self.send_response(500)
        elif ( len(HTTPHandler.credentials) > 0 ):
            if self._checkAuth():
                self.send_response(200)
            else:
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Test')
        else:
            self.send_response(200)

        self.send_header('Content-type', CONTENT_TYPE)
        self.end_headers()

        self._record()

    def do_POST(self):
        body = ''

        if self.path == '/fail':
            self.send_response(self._generateRandomCode())
        elif self.path == '/delayed':
            time.sleep(self._generateDelay())
            self.send_response(500)
        elif ( len(HTTPHandler.credentials) > 0 and not self._checkAuth() ):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Test')
        else:
            try:
                if 'content-length' in self.headers:
                    length = int(self.headers['content-length'])
                    body = str(self.rfile.read(length), "utf-8") if length > 0 else ''
                json.loads(body)
                self.send_response(200)
            except:
                self.send_response(400)

        self.send_header('Content-type', CONTENT_TYPE)
        self.end_headers()

        self._record(body)

    def _record(self, body=''):
        with lock:
            if self.path not in DummyHandler._stats:
                DummyHandler._stats[self.path] = 0
            DummyHandler._stats[self.path] += 1
            DummyHandler._history.append({
                'path': self.path,
                'verb':self.command ,
                'body': body,
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
            print("Matching {} with {}".format(credentials, expected))
            return credentials == expected
        except:
            print("No Authorization header present")
            return False