FROM ubuntu:16.04@sha256:97b54e5692c27072234ff958a7442dde4266af21e7b688e7fca5dc5acc8ed7d9

ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

RUN apt-get update -q && \
    apt-get install -qy \
        git \
        wget \
        make \
        autotools-dev \
        autoconf \
        libtool \
        xz-utils \
        libssl-dev \
        zlib1g-dev \
        libffi-dev \
        libncurses5-dev \
        libsqlite3-dev \
        libusb-1.0-0-dev \
        libudev-dev \
        gettext \
        libzbar0  \
        libdbus-1-3 \
        && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get autoremove -y && \
    apt-get clean
