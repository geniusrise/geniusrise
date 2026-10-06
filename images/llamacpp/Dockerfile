ARG LLAMA_VERSION=b4XXX
FROM ghcr.io/ggml-org/llama.cpp:server-${LLAMA_VERSION}
COPY geniusrise /usr/local/bin/geniusrise
ENV GR_ENGINE_PORT=8080 HF_HOME=/tmp/hf
ENTRYPOINT ["geniusrise"]
CMD ["node"]
