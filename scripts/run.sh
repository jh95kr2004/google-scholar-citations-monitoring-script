#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
SC_PATH="${SCRIPT_PATH}/../screenshots"
CONDA_PATH=`which conda`
CONDA_ENV="py3_chrome_selenium"
KAKAO_REST_API_KEY=""
KAKAO_ID=""
KAKAO_PW=""
CHECK_INTERVAL="10"
DOMAIN=""
HTTP_PORT="8080"

activate_env() {
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV}"
}

run() {
    cd "${SCRIPT_PATH}"
    python ../python/main.py \
        --sc_path "${SC_PATH}" \
        --kakao_rest_api_key "${KAKAO_REST_API_KEY}" \
        --kakao_id "${KAKAO_ID}" \
        --kakao_pw "${KAKAO_PW}" \
        --check_interval "${CHECK_INTERVAL}" \
        --domain "${DOMAIN}" \
        --http_port "${HTTP_PORT}"
}

main() {
    OSITIONAL_ARGS=()

    while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--kakao-rest-api-key)
        KAKAO_REST_API_KEY="$2"
        shift # past argument
        shift # past value
        ;;
        -u|--kakao-id)
        KAKAO_ID="$2"
        shift # past argument
        shift # past value
        ;;
        -w|--kakao-pw)
        KAKAO_PW="$2"
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
