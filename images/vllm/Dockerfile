ARG VLLM_VERSION=0.11.0
FROM vllm/vllm-openai:${VLLM_VERSION}
COPY geniusrise /usr/local/bin/geniusrise
ENV GR_ENGINE_PORT=8000
ENTRYPOINT ["geniusrise"]
CMD ["node"]
