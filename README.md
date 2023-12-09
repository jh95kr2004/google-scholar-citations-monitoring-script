# Google Scholar Citations Monitoring Script

Simple Python script which monitors the changing of the number of citations every 5 mins (configurable) via Google Scholar. If the number increases/decreases, the script will send an email to you as a notification.

## Environment

Only tested on Ubuntu 20.04, but logically should be working on most Linux/Unix system.

## Requirments
You can run the script on your host OS or on a docker container. Using docker is recommended to isolate the environment and prevent potential conflicts with other products on your host.

### Host OS
- [Conda](https://docs.conda.io/projects/miniconda/en/latest/)

### Docker (Recommended)
- [Docker](https://docs.docker.com/engine/install/)

## Prepare Google account

## Build

### Host OS
Run the following script to create a conda env and install required packages automatically.
```
$ ./scripts/install.sh
```

### Docker
Run the following script to build a docker image which contains all required packages.
```
$ ./docker/build.sh
```

## Run

Before running the script, open the `./scripts/run.sh` or `./docker/run.sh` file accordingly and update the following variables.

- **SCHOLAR_URL** (required): The Google Scholar URL to be monitored. (e.g., https://scholar.google.com/citations?user=DdhlAfgAAAAJ&hl=en)
- **GMAIL_ID** (required): Your Google account (including `@gmail.com`) to login gmail service and send notification emails to yourself.
- **GMAIL_PW** (required): Create an app password and set it to this variable. It is *NOT* your original Google account password. (See https://support.google.com/accounts/answer/185833?hl=en)
- **DOMAIN** (optional): The script will start a simple HTTP server to update or see the last citations number. If you pass your own domain, you can access the server via the domain. Otherwise, you can access it only locaaly.
- **CHECK_INTERVAL** (optional): the period of updating the citations numbers. (default is 300s)

### Host OS
```
$ ./scripts/run.sh
```

### Docker
```
$ ./docker/run.sh
```

If you want to run the container as a deamon, pass `-dm` or `--daemon` argument.
```
$ ./docker/run.sh -dm
```

## HTTP server
The script creates a [Flask](https://flask.palletsprojects.com/) instance to have a simple HTTP server. Its default port is `8080` and you can manually change it from the `run.sh` scripts accordingly.

### API

If you have passed your own domain to the `DOMAIN` variable at the [Run](#run) step, you can access the server with your domain address. Otherwise, you can access the server via http://127.0.0.1.

#### /citations/update
Updates the number of citations and returns it.

#### /citations/latest
Returns the last updated number of citations.

## Stop

### Host OS
Simply input `Ctrl-C` to stop the script.

### Docker
If you are not running the container as a daemon (i.e., you didn't pass `-dm` or `--daemon` arg), input `Ctrl-C` to stop the script.

Otherwise, use the [docker/stop.sh](docker/stop.sh) script to stop the container easily.
```
$ ./docker/stop.sh
```