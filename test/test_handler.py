import pytest

import base64
import json
import requests
import ssl
import threading

from dummyserver import handler
from dummyserver import server

SERVER_CRT = "test/test_handler/server-bundle.crt"
SERVER_CA  = "test/test_handler/rootCA.crt"
CLIENT_CRT = "test/test_handler/client.crt"
CLIENT_KEY = "test/test_handler/client.key"
CLIENT_CA  = "test/test_handler/rootCA.crt"

HTTP_PORT   = 8080
HTTPS_PORT  = 8181
HTTPSM_PORT = 8282
MGMT_PORT   = 8383

USERNAME = "testuser"
PASSWORD = "testpass"
CREDENTIALS = base64.b64encode(b"testuser:testpass")

ERROR_RANGE = list(range(402, 418))+list(range(500, 505))

@pytest.fixture(scope="module")
def mgmt_server():
    # Startup
    print("Starting server")
    http_server = server.ThreadedHTTPServer(("", MGMT_PORT), handler.DummyHandler)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.setDaemon(True)
    http_thread.start()
    yield http_server
    # Teardown
    print("Stopping server")
    http_server.shutdown()
    http_server.server_close()

@pytest.fixture(scope="module")
def http_server_with_credentials():
    # Startup
    print("Starting server")
    http_server = server.ThreadedHTTPServer(("", HTTP_PORT), handler.HTTPHandler)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.setDaemon(True)
    http_thread.start()
    yield http_server
    # Teardown
    print("Stopping server")
    http_server.shutdown()
    http_server.server_close()

@pytest.fixture(scope="module")
def https_server_with_credentials():
    # Startup
    print("Starting server")
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.verify_mode = ssl.CERT_NONE
    context.load_cert_chain(certfile=SERVER_CRT)
    handler.HTTPHandler.credentials = CREDENTIALS
    https_server = server.ThreadedHTTPServer(("", HTTPS_PORT), handler.HTTPHandler)
    https_server.socket = context.wrap_socket (https_server.socket, server_side=True)
    https_thread = threading.Thread(target=https_server.serve_forever)
    https_thread.setDaemon(True)
    https_thread.start()
    yield https_server
    # Teardown
    print("Stopping server")
    https_server.shutdown()
    https_server.server_close()

@pytest.fixture(scope="module")
def https_server_with_mutual_auth_with_credentials():
    # Startup
    print("Starting server")
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile=SERVER_CRT)
    context.load_verify_locations(cafile=CLIENT_CA)
    handler.HTTPHandler.credentials = CREDENTIALS
    https_server = server.ThreadedHTTPServer(("", HTTPSM_PORT), handler.HTTPHandler)
    https_server.socket = context.wrap_socket (https_server.socket, server_side=True)
    https_thread = threading.Thread(target=https_server.serve_forever)
    https_thread.setDaemon(True)
    https_thread.start()
    yield https_server
    # Teardown
    print("Stopping server")
    https_server.shutdown()
    https_server.server_close()

def test_http_with_credentials(http_server_with_credentials):
    r = requests.get(
        url = 'http://localhost:{}'.format(HTTP_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.status_code == 200

def test_http_with_credentials_fail_url(http_server_with_credentials):
    r = requests.get(
        url = 'http://localhost:{}/fail'.format(HTTP_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.status_code in ERROR_RANGE

def test_https_with_credentials(https_server_with_credentials):
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPS_PORT),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.status_code == 200

def test_https_with_credentials_ignore_client_cert(https_server_with_credentials):
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPS_PORT),
        cert=(CLIENT_CRT, CLIENT_KEY),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.status_code == 200

def test_https_with_mutual_auth_with_credentials(https_server_with_mutual_auth_with_credentials):
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPSM_PORT),
        cert=(CLIENT_CRT, CLIENT_KEY),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.status_code == 200

def test_https_with_mutual_auth_with_credentials_wrong_password(https_server_with_mutual_auth_with_credentials):
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPSM_PORT),
        cert=(CLIENT_CRT, CLIENT_KEY),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, '')
    )
    assert r.status_code == 401

def test_https_with_mutual_auth_with_credentials_ssl_failure(https_server_with_mutual_auth_with_credentials):
    with pytest.raises(requests.exceptions.SSLError):
        r = requests.get(
            url = 'https://localhost:{}'.format(HTTPSM_PORT),
            verify=SERVER_CA,
            auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
        )

def test_mgmt_clear(mgmt_server, https_server_with_credentials):
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPS_PORT),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'http://localhost:{}/clear'.format(MGMT_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'http://localhost:{}/stats'.format(MGMT_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.content == b'{}'

def test_mgmt_stats(mgmt_server, https_server_with_credentials, https_server_with_mutual_auth_with_credentials):
    r = requests.get(
        url = 'http://localhost:{}/clear'.format(MGMT_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPS_PORT),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPSM_PORT),
        cert=(CLIENT_CRT, CLIENT_KEY),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'https://localhost:{}/fail'.format(HTTPSM_PORT),
        cert=(CLIENT_CRT, CLIENT_KEY),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'http://localhost:{}/stats'.format(MGMT_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    assert r.content == b'{"/": 2, "/fail": 1}'

def test_mgmt_history(mgmt_server, https_server_with_credentials):
    r = requests.get(
        url = 'http://localhost:{}/clear'.format(MGMT_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'https://localhost:{}'.format(HTTPS_PORT),
        verify=SERVER_CA,
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    r = requests.get(
        url = 'http://localhost:{}/history'.format(MGMT_PORT),
        auth=requests.auth.HTTPBasicAuth(USERNAME, PASSWORD)
    )
    content = json.loads(r.content)
    assert len(content) == 1
    assert content[0]["path"] == '/'
    assert content[0]["verb"] == 'GET'