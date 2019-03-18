#!/usr/bin/env python3

import base64
import json
import logging
import os
import random
import ssl
import threading

from dummyserver import handler
from dummyserver import server

HTTP_PORT   = int(os.environ.get('HTTP_PORT', 8080))
HTTPS_PORT  = int(os.environ.get('HTTPS_PORT', 8181))
HTTPSM_PORT = int(os.environ.get('HTTPSM_PORT', 8282))
MGMT_PORT   = int(os.environ.get('MGMT_PORT', 8383))

CREDENTIALS = base64.b64encode(os.environ.get('CREDENTIALS', '').encode('UTF'))

SERVER_CRT  = os.environ.get('SERVER_CRT_PATH', '/etc/ssl/certs/dummy.crt').encode('UTF')
CLIENT_CA   = os.environ.get('CLIENT_CA_PATH', '/etc/ssl/certs/dummy_ca.crt').encode('UTF')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

LOGGER = logging.getLogger(__name__)

def main():
    # TODO: make this a bit more customizable
    handler.HTTPHandler.credentials = CREDENTIALS

    # Create HTTP Endpoint
    http_server = server.ThreadedHTTPServer(("", HTTP_PORT), handler.HTTPHandler)
    LOGGER.info("Serving HTTP server on port: {}".format(HTTP_PORT))
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.setDaemon(True)
    http_thread.start()

    # Create HTTPS Endpoint
    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=SERVER_CRT)
    https_server = server.ThreadedHTTPServer(("", HTTPS_PORT), handler.HTTPHandler)
    https_server.socket = context.wrap_socket (https_server.socket, server_side=True)
    LOGGER.info("Serving HTTPS server on port: {}".format(HTTPS_PORT))
    https_thread = threading.Thread(target=https_server.serve_forever)
    https_thread.setDaemon(True)
    https_thread.start()

    # Create HTTPS Mutual Endpoint
    contextm = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    contextm.verify_mode = ssl.CERT_REQUIRED
    contextm.load_cert_chain(certfile=SERVER_CRT)
    contextm.load_verify_locations(cafile=CLIENT_CA)
    httpsm_server = server.ThreadedHTTPServer(("", HTTPSM_PORT), handler.HTTPHandler)
    httpsm_server.socket = contextm.wrap_socket (httpsm_server.socket, server_side=True)
    LOGGER.info("Serving HTTPS mutual authentication server on port: {}".format(HTTPSM_PORT))
    httpsm_thread = threading.Thread(target=httpsm_server.serve_forever)
    httpsm_thread.setDaemon(True)
    httpsm_thread.start()

    # Create Management Endpoint
    mgmt_server = server.ThreadedHTTPServer(("", MGMT_PORT), handler.DummyHandler)
    LOGGER.info("Serving DUMMY server on port: {}".format(MGMT_PORT))
    mgmt_server.serve_forever()

if __name__ == '__main__':
    main()