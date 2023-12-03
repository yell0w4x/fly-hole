FROM rust:1.74.0-bullseye AS relay-build

COPY relay/rust /app/

WORKDIR /app
RUN cargo build --release

###
FROM pihole/pihole:latest
COPY --from=relay-build /app/target/release/relay /app/relay

RUN apt-get update --yes -o APT::Update::Error-Mode=any
RUN apt-get install -y --no-install-recommends htop

COPY start.sh /app/
COPY wait-for-it.sh /app/

WORKDIR /app

ENTRYPOINT ["/bin/bash", "/app/start.sh", "--rust"]

