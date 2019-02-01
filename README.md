# Dummy Webserver

This is just a dummy webserver. All the requests are recorded.
It will answer 200 to GET requests and to POST requests with a valid json body. In case of validation error when parsing the json body it will return a 418.

It has 4 special paths:

- /dummy/stats prints how many times a particular path has been called
- /dummy/history prints the recorded history of all the requests
- /dummy/clear resets the history and the stats.
- /fail returns an error code