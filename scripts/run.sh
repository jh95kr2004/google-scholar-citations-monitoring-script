#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
SC_PATH="${SCRIPT_PATH}/../screenshots"
LOG_PATH="${SCRIPT_PATH}/../log"
LOG_FILE="log.txt"
LOG_LEVEL="debug"
CONDA_PATH=`which conda`
CONDA_ENV="py3_chrome_selenium"
GMAIL_ID=""
GMAIL_PW=""
CHECK_INTERVAL="300"
DOMAIN=""
HTTP_PORT="8080"
SENDER_TYPE="gmail"

activate_env() {
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV}"
}

run() {
    cd "${SCRIPT_PATH}/.."
    python -m python.citations \
        --sc_path "${SC_PATH}" \
        --gmail_id "${GMAIL_ID}" \
        --gmail_pw "${GMAIL_PW}" \
        --check_interval "${CHECK_INTERVAL}" \
        --domain "${DOMAIN}" \
        --http_port "${HTTP_PORT}" \
        --log_path "${LOG_PATH}" \
        --log_file "${LOG_FILE}" \
        --log_level "${LOG_LEVEL}" \
        --sender_type "${SENDER_TYPE}"
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
        *)
        POSITIONAL_ARGS+=("$1") # save positional arg
        shift # past argument
        ;;
    esac
    done

    set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

    activate_env
    run
}

main "$@"
