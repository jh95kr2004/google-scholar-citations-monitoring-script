#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
SC_PATH="${SCRIPT_PATH}/../screenshots"
LOG_PATH="${SCRIPT_PATH}/../log"
LOG_FILE="log.txt"
LOG_LEVEL="debug"
GMAIL_ID=""
GMAIL_PW=""
CHECK_INTERVAL="300"
DOMAIN=""
HTTP_PORT="8080"
SENDER_TYPE="gmail"
DOCKER_IMAGE_TAG="hanseung-lee-citations"
DOCKER_CONTAINER_NAME="hanseung-lee-citations"
DAEMON=false

run_container() {
    docker_args="-it"
    if [[ "${DAEMON}" = true ]]; then
        docker_args="-d"
    fi

    uid=$(id -u)
    gid=$(id -g)
    mkdir -p "${HOME}/.cache"

    docker run "${docker_args}" --rm \
        --user $uid:$gid \
        -p "${HTTP_PORT}":"${HTTP_PORT}" \
        --name "${DOCKER_CONTAINER_NAME}" \
        -v "${SC_PATH}":/opt/hanseung-lee-citations/screenshots \
        -v "${LOG_PATH}":/opt/hanseung-lee-citations/log \
        -v "${HOME}/.cache:/.cache" \
        "${DOCKER_IMAGE_TAG}" \
        -gid "${GMAIL_ID}" \
        -gpw "${GMAIL_PW}" \
        -i "${CHECK_INTERVAL}" \
        -d "${DOMAIN}" \
        -p "${HTTP_PORT}" \
        -lf "${LOG_FILE}" \
        -ll "${LOG_LEVEL}" \
        -st "${SENDER_TYPE}"
}

main() {
    OSITIONAL_ARGS=()

    while [[ $# -gt 0 ]]; do
    case $1 in
        -gid|--gmail-id)
        GMAIL_ID="$2"
        shift # past argument
        shift # past value
        ;;
        -gpw|--gmail-pw)
        GMAIL_PW="$2"
        shift # past argument
        shift # past value
        ;;
        -i|--check-interval)
        CHECK_INTERVAL="$2"
        shift # past argument
        shift # past value
        ;;
        -d|--domian)
        DOMAIN="$2"
        shift # past argument
        shift # past value
        ;;
        -p|--port)
        HTTP_PORT="$2"
        shift # past argument
        shift # past value
        ;;
        -lp|--log-path)
        LOG_PATH="$2"
        shift # past argument
        shift # past value
        ;;
        -lf|--log-file)
        LOG_FILE="$2"
        shift # past argument
        shift # past value
        ;;
        -ll|--log-level)
        LOG_LEVEL="$2"
        shift # past argument
        shift # past value
        ;;
        -st|--sender-type)
        SENDER_TYPE="$2"
        shift # past argument
        shift # past value
        ;;
        -dm|--daemon)
        DAEMON=true
        shift # past argument
        ;;
        *)
        POSITIONAL_ARGS+=("$1") # save positional arg
        shift # past argument
        ;;
    esac
    done

    set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

    mkdir -p "${SC_PATH}"
    mkdir -p "${LOG_PATH}"
    run_container
}

main "$@"