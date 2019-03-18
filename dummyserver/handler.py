import http.server
import json
import random
import threading

lock = threading.Lock()

class BaseHTTPHandler(http.server.BaseHTTPRequestHandler):
    pass

class DummyHandler(BaseHTTPHandler):

    _stats = {}
    _history = []

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()

        if self.path == '/stats':
            self.wfile.write(json.dumps(self._getStats()).encode('UTF-8'))
        elif self.path == '/history':
            self.wfile.write(json.dumps(self._getHistory()).encode('UTF-8'))
        elif self.path == '/clear':
            self._clear()
        return

    def _clear(self):
        DummyHandler._stats = {}
        DummyHandler._history = []

    def _getStats(self):
        return DummyHandler._stats

    def _getHistory(self):
        return DummyHandler._history

class HTTPHandler(BaseHTTPHandler):

    def __init__(self, credentials):
        self.credentials = credentials

    def do_GET(self):
        if self.path == '/fail':
            self.send_response(self._generateRandomCode())
        elif ( len(self.credentials) > 0 ):
            if self._checkAuth():
                self.send_response(200)
            else:
                self.send_response(401)
                self.send_header('WWW-Authenticate', 'Test')
        else:
            self.send_response(200)

        self.send_header('Content-type','application/json')
        self.end_headers()

        self._record()
        return

    def do_POST(self):
        body = ''

        if self.path == '/fail':
            self.send_response(self._generateRandomCode())
        elif ( len(self.credentials) > 0 and not self._checkAuth() ):
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

        self.send_header('Content-type','application/json')
        self.end_headers()

        self._record(body)
        return

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

    def _checkAuth(self):
        try:
            credentials = self.headers['Authorization']
            expected = 'Basic ' + self.credentials.decode('UTF')
            print("Matching {} with {}".format(credentials, expected))
            return credentials == expected
        except:
            print("No Authorization header present")
            return False