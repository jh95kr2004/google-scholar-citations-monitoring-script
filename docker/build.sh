#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
DOCKER_IMAGE_TAG="hanseung-lee-citations"

cd "${SCRIPT_PATH}/.."
docker build -t "${DOCKER_IMAGE_TAG}" .