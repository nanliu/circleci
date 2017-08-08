FROM ubuntu:16.04

ARG KUBERNETES_VERSION="v1.6.4"
ARG HELM_VERSION="v2.5.0"
ARG DOCKER_VERSION="17.06.0~ce-0~ubuntu"

RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    software-properties-common \
    curl \
    git-crypt \
    jq \
    parallel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBERNETES_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl
RUN curl -L http://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -o /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    tar xzf /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    mv linux-amd64/helm /usr/local/bin &&\
    rm /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && rm -r linux-amd64
RUN chmod 755 /usr/local/bin/*

RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

RUN add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

RUN apt-get update && apt-get install -y \
    docker-ce=${DOCKER_VERSION} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# NOTE: Silent parallel
RUN echo "will cite\n" > parallel --bibtex
