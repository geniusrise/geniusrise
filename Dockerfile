FROM nvidia/cuda:12.2.0-runtime-ubuntu20.04 AS base

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN useradd --create-home appuser

RUN apt-get update \
 && apt-get install -y software-properties-common build-essential curl wget vim libpq-dev  \
 && add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y python3.10 python3.10-dev python3.10-distutils \
 && apt-get clean
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
 && python3.10 get-pip.py



COPY --chown=appuser:appuser . /app/

RUN pip3.10 install -r requirements.txt
USER appuser

ENTRYPOINT ["genius --help"]
