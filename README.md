# Dummy Webserver

This is just a dummy webserver. All the requests are recorded.
It will answer 200 to GET requests and to POST requests with a valid json body. In case of validation error when parsing the json body it will return a 418.

It exposes 3 different endpoints:

- HTTP: responds to GET/POST requests. Special paths:
  - /fail returns an error code
- HTTPS: responds to GET/POST requests. Special paths:
  - /fail returns an error code
- MANAGEMENT: Special paths:
  - /stats prints how many times a particular path has been called
  - /history prints the recorded history of all the requests
  - /clear resets the history and the stats.

There are few customizations doable via environment variables:

- HTTP_PORT: port for the HTTP endpoint
- HTTPS_PORT: port for the HTTPS endpoint
- MGMT_PORT: port for the managements endpoint
- CREDENTIALS: credentials for basic auth in the "username:password" format
- CERTIFICATE: path to a mounted custom certificate
