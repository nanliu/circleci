#!/usr/bin/env bash
set -eu -o pipefail

export CIRCLECI_CLI_TOKEN="${CIRCLE_TOKEN}"

ORG_NAME="${ORG_NAME}"
TARGET_REPONAME="${TARGET_REPONAME}"
HELM_BRANCH="${HELM_BRANCH:-master}"
STATUS_URL="https://api.github.com/repos/${ORG_NAME}/${CIRCLE_PROJECT_REPONAME}/statuses/${CIRCLE_SHA1}"
build=$(circleci trigger "${ORG_NAME}/${TARGET_REPONAME}" "${HELM_BRANCH}" -K CUSTOM_VALUES -V "${CUSTOM_VALUES}" -K STATUS_URL -V "${STATUS_URL}" -K PR_URL -V "${CIRCLE_PULL_REQUESTS}")

build_id=$(echo "${build}" | jq '.build_num')
[[ -n "${build_id}" ]] || (echo "${build}" && exit 1)
echo "https://circleci.com/gh/${ORG_NAME}/${TARGET_REPONAME}/${build_id}"

curl \
  --header "Authorization: token ${GH_OAUTH_TOKEN}" \
  --request POST "${STATUS_URL}" \
  --data @- <<EOF
  {
    "state": "pending",
    "target_url": "https://circleci.com/gh/${ORG_NAME}/${TARGET_REPONAME}/${build_id}",
    "description": "The integration build ${build_id} started",
    "context": "ci/circleci-integration"
  }
EOF
