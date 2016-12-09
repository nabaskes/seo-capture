# build a custom docker image for running the SEO server
FROM ubuntu:14.04
MAINTAINER Remy Prechelt <rprechelt@uchicago.edu>
ADD . /code
WORKDIR /code
# RUN deb http://httpredir.debian.org/debian/ experimental main contrib non-free
# RUN deb-src http://httpredir.debian.org/debian/ experimental main contrib non-free
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y libzmq3-dev
RUN pip3 install -r /code/requirements.txt