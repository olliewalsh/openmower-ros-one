FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    xz-utils \
    dpkg-dev \
    curl \
    debhelper \
    devscripts \
    dh-python \
    dput \
    libdistro-info-perl \
    fakeroot \
    git \
    gnupg \
    python3 \
    python3-yaml \
    quilt \
    && install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://ros.packages.techfak.net/gpg.key -o /etc/apt/keyrings/ros-one-keyring.gpg \
    && printf 'deb [signed-by=/etc/apt/keyrings/ros-one-keyring.gpg] https://ros.packages.techfak.net noble main\n' > /etc/apt/sources.list.d/ros-one.list \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
