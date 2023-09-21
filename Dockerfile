FROM nvidia/cuda:12.2.0-runtime-ubuntu20.04 AS base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN useradd --create-home genius

RUN apt-get update \
 && apt-get install -y software-properties-common build-essential curl wget vim libpq-dev pkg-config \
 && add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y python3.10 python3.10-dev python3.10-distutils \
 && apt-get clean
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
 && python3.10 get-pip.py

RUN apt-get update && apt-get install -y \libmysqlclient-dev libldap2-dev libsasl2-dev libssl-dev && apt-get clean

RUN pip install geniusrise-listeners
RUN pip install geniusrise-databases
RUN pip install geniusrise-huggingface
RUN pip install geniusrise-openai
RUN pip install --upgrade geniusrise
ENV GENIUS=/home/genius/.local/bin/genius

COPY --chown=genius:genius . /app/

RUN pip3.10 install -r requirements.txt
USER genius

CMD ["genius", "--help"]
