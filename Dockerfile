FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y wget sudo gnupg tzdata
RUN wget "https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh" \
    && chmod 755 Miniconda3-py39_4.12.0-Linux-x86_64.sh
RUN bash Miniconda3-py39_4.12.0-Linux-x86_64.sh -b -p /opt/miniconda3
RUN rm -f Miniconda3-py39_4.12.0-Linux-x86_64.sh
ENV PATH=/opt/miniconda3/bin:${PATH}

WORKDIR /opt/hanseung-lee-citations
COPY scripts/install.sh scripts/install.sh
RUN bash scripts/install.sh && rm scripts/install.sh
COPY scripts/run.sh scripts/run.sh
COPY python python
RUN chmod -R 777 /opt/hanseung-lee-citations

ENTRYPOINT ["scripts/run.sh"]