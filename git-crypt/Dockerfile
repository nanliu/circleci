FROM circleci/python:2.7

USER root
RUN apt-get update && apt-get install -y \
    git-buildpackage \
    xsltproc docbook-xml docbook-xsl

WORKDIR /tmp

RUN git clone https://github.com/AGWA/git-crypt.git && cd /tmp/git-crypt && git checkout debian && git-buildpackage -uc -us
