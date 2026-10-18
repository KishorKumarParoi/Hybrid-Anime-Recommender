FROM tensorzero/gateway:latest

COPY tensorzero.toml /app/tensorzero.toml
COPY templates /app/templates

WORKDIR /app
CMD ["tensorzero-gateway", "--config", "tensorzero.toml"]
