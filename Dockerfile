# syntax = docker/dockerfile:1.2

FROM iwanvosloo/reahl-dev:7.0

ARG GEMSTONE_VERSION=3.7.2
ARG DEV_HOME=/home/developer
ARG DEV_USER=developer

ENV GEMSTONE_VERSION=3.7.2
ENV DEBIAN_FRONTEND=noninteractive


RUN apt-get update --allow-releaseinfo-change-origin && \
    apt-get install --no-install-recommends -y  python3 iputils-ping && \
    apt-get clean && \
    rm -rf /var/cache/apt/* 

COPY ./gemstone /opt/dev/gemstone
COPY ./scripts /opt/dev/scripts

USER root
RUN --mount=type=cache,target=/home/developer/cache /opt/dev/gemstone/installGemStone.sh $GEMSTONE_VERSION
RUN echo 'developer:developer' | chpasswd

USER developer

RUN mkdir -p $DEV_HOME/.reahlworkspace/dist-egg
RUN /opt/dev/gemstone/defineGemStoneEnvironment.sh $GEMSTONE_VERSION

USER root

