#!/bin/bash -xe

VERSION=3.5.2

apt-get install make build-essential libssl-dev zlib1g-dev libbz2-dev libsqlite3-dev
cd /tmp
#wget https://www.python.org/ftp/python/$VERSION/Python-$VERSION.tgz
#tar -xvf Python-$VERSION.tgz
cd Python-$VERSION
./configure
sudo make
sudo make install
