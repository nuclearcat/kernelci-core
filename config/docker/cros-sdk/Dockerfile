# syntax=docker/dockerfile:1
FROM debian:bullseye-slim
MAINTAINER "KernelCI TSC" <kernelci-tsc@groups.io>

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        sudo \
        ca-certificates \
        netbase \
	git \
	build-essential \
	python3 \
	curl \
	wget \
	ssh \
    && apt-get clean \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -u 996 -ms /bin/sh user && adduser user sudo && echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN mkdir -p /home/user/chromiumos && chown -R user /home/user/chromiumos

# Extra packages needed by kernelCI
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3.9 \
    python3-requests \
    python3-yaml

USER user
ENV HOME=/home/user

WORKDIR /kernelci-core
