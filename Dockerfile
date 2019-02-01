FROM alpine:3.8

RUN apk add --no-cache python3

COPY ./src/server /usr/local/bin/server

EXPOSE 8080

CMD [ "/usr/local/bin/server"]