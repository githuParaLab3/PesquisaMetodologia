# Rust 1.86 (compilador 1.88 requerido pelo actix-web para compilar)
FROM rust:1.88-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app
COPY Cargo.toml .
RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release --quiet
COPY src ./src
RUN touch src/main.rs && cargo build --release --quiet

FROM alpine:3.20
RUN apk add --no-cache libgcc
WORKDIR /app
COPY --from=builder /app/target/release/server .
EXPOSE 8083
CMD ["./server"]
