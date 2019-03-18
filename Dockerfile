# Build container

FROM alpine:3.8 as build

RUN apk add build-base curl git make python3 python3-dev

RUN ln -s /usr/bin/python3 /usr/local/bin/python3

COPY . /opt/dummyserver

WORKDIR /opt/dummyserver

RUN make clean
RUN make package

# Distribution container

FROM alpine:3.8

COPY --from=build /opt/dummyserver/dist/dummyserver-*.tar.gz /tmp/dummyserver.tar.gz
COPY ./script/entrypoint /entrypoint

RUN apk add --no-cache curl python3 openssl && \
    curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    python3 /tmp/get-pip.py && \
    pip install /tmp/dummyserver.tar.gz && \
    rm -f /tmp/get-pip.py /tmp/dummyserver.tar.gz

EXPOSE 8080 8181 8282 8383

ENTRYPOINT [ "/entrypoint"]