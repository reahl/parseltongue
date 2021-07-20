# syntax = docker/dockerfile:1.2

FROM iwanvosloo/reahl-dev:5.1

ARG GEMSTONE_VERSION=3.6.1
ARG DEV_HOME=/home/developer
ARG DEV_USER=developer

ENV GEMSTONE_VERSION=3.6.1
ENV DEBIAN_FRONTEND=noninteractive


#sed -i 's|winswitch|xpra|g' /etc/apt/sources.list.d/xpra.list && \
#    rm /etc/apt/sources.list.d/xpra.list && \

RUN apt-get update --allow-releaseinfo-change-origin && \
    apt-get install --no-install-recommends -y build-essential g++ gcc gdb libpam0g-dev iputils-ping python3-dev && \
    apt-get clean && \
    rm -rf /var/cache/apt/* 

COPY ./gemstone /opt/dev/gemstone
COPY ./scripts /opt/dev/scripts

USER root
RUN --mount=type=cache,target=/home/developer/cache /opt/dev/gemstone/installGemStone.sh $GEMSTONE_VERSION
#RUN /opt/dev/gemstone/installGemStone.sh $GEMSTONE_VERSION
RUN echo 'developer:developer' | chpasswd

USER developer

RUN mkdir -p $DEV_HOME/.reahlworkspace/dist-egg
#RUN /opt/dev/scripts/setupGit.sh
RUN /opt/dev/gemstone/defineGemStoneEnvironment.sh $GEMSTONE_VERSION
RUN bash -lc "pip install cython"

USER root

