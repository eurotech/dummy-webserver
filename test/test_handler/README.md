# Certificate generation

``` Shell
openssl genrsa -out rootCA.key 4096
openssl req -x509 -new -nodes -key rootCA.key -sha256 -days 3000 -out rootCA.crt -subj "/C=US/ST=CA/O=MyOrg, Inc./CN=rootca"

openssl genrsa -out server.key 2048
openssl genrsa -out client.key 2048

openssl req -new -key server.key -out server.csr -subj "/C=US/ST=CA/O=MyOrg, Inc./CN=client" -config server.req
openssl req -new -key client.key -out client.csr -subj "/C=US/ST=CA/O=MyOrg, Inc./CN=client" -config server.req

openssl x509 -req -in server.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out server.crt -days 2500 -sha256 -extfile server.req -extensions req_ext
openssl x509 -req -in client.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out client.crt -days 2500 -sha256 -extfile client.req -extensions req_ext

cat server.key server.crt rootCA.crt > server-bundle.crt
```