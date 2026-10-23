FROM rust:1.82-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src/ ./src/
RUN cargo build --release

FROM alpine:3.19
WORKDIR /root/
COPY --from=builder /app/target/release/rust-scoring-engine .
EXPOSE 8083
CMD ["./rust-scoring-engine"]
