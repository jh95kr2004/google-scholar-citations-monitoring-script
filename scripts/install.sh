#!/bin/bash

SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
CONDA_PATH=`which conda`
CONDA_ENV="py3_chrome_selenium"

error() {
    echo "$1"
    exit 1
}

install_chrome() {
    if dpkg -s google-chrome-stable >/dev/null 2>&1; then
        error "google-chrome-stable is already installed, remove it and retry this script"
    fi

    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    if ! sudo apt -y install ./google-chrome-stable_current_amd64.deb; then
        error "Failed to install Chrome"
    fi
}

check_conda() {
    if ! [[ -x "${CONDA_PATH}" ]]; then
        error "Please install conda"
    fi
    echo "Use conda: ${CONDA_PATH}"
}

create_env() {
    if conda env list | grep ".*${CONDA_ENV}.*" >/dev/null 2>&1; then
        error "Conda already has \"${CONDA_ENV}\" env, please check and remove it or try with another env name using '--env' argument"
    fi

    echo "Create conda env: ${CONDA_ENV}"

    if ! conda create -y -n "${CONDA_ENV}" python=3 selenium requests flask -c conda-forge; then
        error "Failed to create conda env"
    fi
}

activate_env() {
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV}"
}

install_packages() {
    pip install chromedriver-binary-auto
}

main() {
    POSITIONAL_ARGS=()

    while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--conda)
        CONDA_PATH="$2"
        shift # past argument
        shift # past value
        ;;
        -e|--env)
        CONDA_ENV="$2"
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

    install_chrome
    check_conda
    create_env
    activate_env
    install_packages
}

main "$@"
