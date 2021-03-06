FROM circleci/python:2.7

USER root
RUN apt-get update && apt-get install -y \
    git-buildpackage \
    xsltproc docbook-xml docbook-xsl

WORKDIR /tmp

RUN git clone https://github.com/AGWA/git-crypt.git && cd /tmp/git-crypt && git checkout debian && git-buildpackage -uc -us

FROM circleci/python:2.7

ARG BUILD_DATE
ARG GIT_SHA1
ARG GIT_TAG

ARG KUBERNETES_VERSION="v1.6.4"
ARG HELM_VERSION="v2.5.1"
ARG TERRAFORM_VERSION="0.11.2"
ARG PACKER_VERSION="1.1.3"
ARG GCLOUD_SDK_VERSION="185.0.0"
# NOTE: Using my branch to fix quoting issue:
ARG CIRCLE_CLI_VERSION="quote"
ARG HUB_VERSION="2.3.0-pre10"

LABEL maintainer="Nan Liu" \
      org.label-schema.name="circleci" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-url="https://github.com/nanliu/circleci" \
      org.label-schema.vcs-ref=$GIT_SHA1 \
      org.label-schema.version=$GIT_TAG

USER root

ENV SHELL "/bin/bash"

RUN apt-get update && apt-get install -y \
    parallel jq gettext cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=0 /tmp/*.deb /tmp/
RUN dpkg -i /tmp/*.deb

RUN curl -sfL https://storage.googleapis.com/kubernetes-release/release/${KUBERNETES_VERSION}/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl && \
    chmod 755 /usr/local/bin/kubectl
RUN curl -sfL https://github.com/nanliu/helm/releases/download/${HELM_VERSION}/helm -o /usr/local/bin/helm && \
    chmod 755 /usr/local/bin/helm
#RUN curl -sfL http://storage.googleapis.com/kubernetes-helm/helm-${HELM_VERSION}-linux-amd64.tar.gz -o /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
#    tar xzf /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && \
#    mv linux-amd64/helm /usr/local/bin && \
#    rm /tmp/helm-${HELM_VERSION}-linux-amd64.tar.gz && rm -r linux-amd64
RUN curl -sfL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -o /tmp/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip /tmp/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    cp terraform /usr/local/bin && \
    rm /tmp/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN curl -sfL https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip -o /tmp/packer_${PACKER_VERSION}_linux_amd64.zip && \
    unzip /tmp/packer_${PACKER_VERSION}_linux_amd64.zip && \
    cp packer /usr/local/bin && \
    rm /tmp/packer_${PACKER_VERSION}_linux_amd64.zip
RUN curl -sfL https://raw.githubusercontent.com/nanliu/circleci-cli/${CIRCLE_CLI_VERSION}/src/circleci -o /usr/local/bin/circleci && \
    chmod 755 /usr/local/bin/circleci
RUN curl -fL https://github.com/github/hub/releases/download/v${HUB_VERSION}/hub-linux-amd64-${HUB_VERSION}.tgz -o /tmp/hub-linux-amd64-${HUB_VERSION}.tgz && \
    tar xzf /tmp/hub-linux-amd64-${HUB_VERSION}.tgz && \
    mv hub-linux-amd64-${HUB_VERSION}/bin/hub /usr/local/bin && \
    rm /tmp/hub-linux-amd64-${HUB_VERSION}.tgz && rm -r hub-linux-amd64-${HUB_VERSION}
RUN curl -sSLo google-cloud-sdk.tar.gz https://storage.googleapis.com/cloud-sdk-release/google-cloud-sdk-${GCLOUD_SDK_VERSION}-linux-x86_64.tar.gz \
    && tar zxf google-cloud-sdk.tar.gz \
    && rm google-cloud-sdk.tar.gz \
    && ./google-cloud-sdk/install.sh --usage-reporting=true --path-update=true \
    && ln -s /google-cloud-sdk/bin/gcloud /usr/local/bin/

RUN pip install -U pip setuptools
COPY . /app
WORKDIR /app
RUN pip install -U .

USER circleci

RUN pip install awscli --upgrade --user
ENV PATH "/home/circleci/.local/bin:${PATH}"

RUN mkdir -p "$(helm home)/plugins" && \
    helm plugin install https://github.com/databus23/helm-diff

# NOTE: Silent parallel
RUN echo "will cite\n" | parallel --bibtex


CMD ["/bin/bash"]
