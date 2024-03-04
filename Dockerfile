# Builder stage: Use the devel image to build and install your application
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04 AS builder

WORKDIR /build

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies and Python
RUN apt-get update \
 && apt-get install -y software-properties-common build-essential curl wget vim git cmake libpq-dev pkg-config \
 && add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y python3.10 python3.10-dev python3.10-distutils \
 && apt-get clean
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
 && python3.10 get-pip.py

RUN pip install --ignore-installed --no-cache-dir --upgrade packaging
RUN pip install --ignore-installed --no-cache-dir --upgrade torch
RUN CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install --ignore-installed --no-cache-dir --upgrade geniusrise
ENV GENIUS=/home/genius/.local/bin/genius

# Runtime stage: Use the runtime image to create a smaller, more secure final image
FROM nvidia/cuda:12.2.0-base-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y software-properties-common build-essential curl wget vim git cmake libpq-dev pkg-config \
 && add-apt-repository ppa:deadsnakes/ppa \
 && apt-get update \
 && apt-get install -y python3.10 python3.10-dev python3.10-distutils \
 && apt-get clean
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
 && python3.10 get-pip.py

WORKDIR /app

# Create a user for running the application
RUN useradd --create-home genius

# Copy the installed Python packages and any other necessary files from the builder image
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /usr/local/bin /usr/local/bin

ENV TZ UTC

USER genius

CMD ["genius", "--help"]
