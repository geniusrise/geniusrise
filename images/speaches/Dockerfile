ARG SPEACHES_VERSION=0.9.0
FROM ghcr.io/speaches-ai/speaches:${SPEACHES_VERSION}
COPY geniusrise /usr/local/bin/geniusrise
ENV GR_ENGINE_PORT=8000
ENTRYPOINT ["geniusrise"]
CMD ["node"]
