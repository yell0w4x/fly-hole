FROM pihole/pihole:latest

RUN apt-get update --yes -o APT::Update::Error-Mode=any
RUN apt-get install -y --no-install-recommends \
    socat net-tools tcpdump tmux strace htop iperf build-essential

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

COPY start.sh /app/
COPY relay/rust /app/
COPY wait-for-it.sh /app/

WORKDIR /app
RUN ~/.cargo/bin/cargo build --release

ENTRYPOINT ["/bin/bash", "/app/start.sh", "--rust"]

