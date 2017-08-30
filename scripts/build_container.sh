#!/usr/bin/env bash
set -eu -o pipefail

if [[ -n "${PIPBOT_PEM:-}" ]]; then
  docker build . \
    -t "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" \
    --build-arg PIPBOT_PEM="${PIPBOT_PEM}" \
    --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
    --build-arg GIT_SHA1="${CIRCLE_SHA1}" \
    --build-arg GIT_TAG="${CIRCLE_TAG:-}"
else
  docker build . \
    -t "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" \
    --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
    --build-arg GIT_SHA1="${CIRCLE_SHA1}" \
    --build-arg GIT_TAG="${CIRCLE_TAG:-}"
fi

MUNGED_BRANCH=$(echo "$CIRCLE_BRANCH" | tr '/' '_')

if [[ -n "${QUAY_USER:-}" ]]; then
  docker login -u "${QUAY_USER}" -p "${QUAY_PASS}" quay.io
  docker tag "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" "quay.io/${QUAY_REPO}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}"
  docker push "quay.io/${QUAY_REPO}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}"

  if [[ -n "${CIRCLE_TAG:-}" ]]; then
    docker tag "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" "quay.io/${QUAY_REPO}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_TAG}"
    docker push "quay.io/${QUAY_REPO}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_TAG}"
  else
    docker tag "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" "quay.io/${QUAY_REPO}/${CIRCLE_PROJECT_REPONAME}:${MUNGED_BRANCH}"
    docker push "quay.io/${QUAY_REPO}/${CIRCLE_PROJECT_REPONAME}:${MUNGED_BRANCH}"
  fi
fi

if [[ -n "${GOOGLE_AUTH:-}" ]]; then
  echo "${GOOGLE_AUTH}" | base64 -d > /tmp/gcp-key.json
  gcloud auth activate-service-account --key-file /tmp/gcp-key.json
  gcloud config set project "${GOOGLE_PROJECT_ID}"
  docker tag "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" "gcr.io/${GOOGLE_PROJECT_ID}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}"
  gcloud docker -- push "gcr.io/${GOOGLE_PROJECT_ID}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}"

  if [[ -n "${CIRCLE_TAG:-}" ]]; then
    docker tag "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" "gcr.io/${GOOGLE_PROJECT_ID}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_TAG}"
    gcloud docker -- push "gcr.io/${GOOGLE_PROJECT_ID}/${CIRCLE_PROJECT_REPONAME}:${CIRCLE_TAG}"
  else
    docker tag "${CIRCLE_PROJECT_REPONAME}:${CIRCLE_SHA1}" "gcr.io/${GOOGLE_PROJECT_ID}/${CIRCLE_PROJECT_REPONAME}:${MUNGED_BRANCH}"
    gcloud docker -- push "gcr.io/${GOOGLE_PROJECT_ID}/${CIRCLE_PROJECT_REPONAME}:${MUNGED_BRANCH}"
  fi
fi
