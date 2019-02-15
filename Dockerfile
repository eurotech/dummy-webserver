FROM alpine:3.8

RUN apk add --no-cache python3 openssl

COPY ./src/server /usr/local/bin/server
COPY ./src/entrypoint /entrypoint

EXPOSE 8080 8181 8282

ENTRYPOINT [ "/entrypoint"]