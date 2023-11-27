FROM pihole/pihole:latest

RUN apt-get update --yes -o APT::Update::Error-Mode=any
RUN apt-get install -y --no-install-recommends \
    socat net-tools tcpdump tmux strace htop iperf python3 python3-pip

COPY start.sh /app/
COPY relay/python /app/
COPY wait-for-it.sh /app/
WORKDIR /app
RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/bash", "/app/start.sh", "--python"]

