FROM ubuntu:16.04

ARG KUBERNETES_VERSION="v1.6.2"
ARG HELM_VERSION="v2.5.0"

RUN apt-get update && apt-get install -y \
    curl \
    git-crypt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBERNETES_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl
RUN curl -L http://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -o /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    tar xzf /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    mv linux-amd64/helm /usr/local/bin &&\
    rm /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && rm -r linux-amd64

