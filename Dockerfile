# Build container

FROM alpine:3.21.2 AS build

RUN apk add build-base curl git make python3 python3-dev

RUN ln -s /usr/bin/python3 /usr/local/bin/python3

COPY . /opt/dummyserver

WORKDIR /opt/dummyserver

RUN make clean
RUN make package

# Distribution container

FROM alpine:3.21.2

COPY --from=build /opt/dummyserver/dist/dummyserver-*.tar.gz /tmp/dummyserver.tar.gz
COPY ./script/entrypoint /entrypoint

RUN apk add --no-cache curl python3 openssl py3-pip py-requests && \
    pip install --break-system-packages /tmp/dummyserver.tar.gz && \
    rm -f /tmp/dummyserver.tar.gz && \
    chmod +x /entrypoint

EXPOSE 8001 8002 8003 8004

ENTRYPOINT [ "/entrypoint" ]
