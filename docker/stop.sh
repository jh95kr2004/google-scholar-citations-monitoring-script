#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
DOCKER_CONTAINER_NAME="hanseung-lee-citations"

docker kill "${DOCKER_CONTAINER_NAME}"