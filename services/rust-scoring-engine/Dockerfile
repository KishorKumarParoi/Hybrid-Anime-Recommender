FROM rust:1.82-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app

# Step 1: Pre-fetch and compile dependencies to cache layer
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src

# Step 2: Compile application source code
COPY src/ ./src/
RUN touch src/main.rs && cargo build --release && strip target/release/rust-scoring-engine

FROM alpine:3.19
WORKDIR /root/
COPY --from=builder /app/target/release/rust-scoring-engine .
EXPOSE 8083
CMD ["./rust-scoring-engine"]
