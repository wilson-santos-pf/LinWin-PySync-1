#!/usr/bin/env bash

# install SSL
cd /usr/src

wget https://www.openssl.org/source/openssl-1.0.2j.tar.gz -O openssl.tar.gz

tar -zxf openssl.tar.gz

cd openssl-*

./config

make

make test

make install

mv /usr/bin/openssl /root/

ln -s /usr/local/ssl/bin/openssl /usr/bin/openssl

openssl version