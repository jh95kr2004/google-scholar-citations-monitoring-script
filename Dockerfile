FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y wget sudo gnupg tzdata
RUN wget "https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh" \
    && chmod 755 Miniconda3-py39_4.12.0-Linux-x86_64.sh
RUN bash Miniconda3-py39_4.12.0-Linux-x86_64.sh -b
RUN rm -f Miniconda3-py39_4.12.0-Linux-x86_64.sh
ENV PATH=/root/miniconda3/bin:${PATH}

WORKDIR /root/work
COPY scripts scripts
RUN bash scripts/install.sh
COPY python python

ENTRYPOINT ["scripts/run.sh"]