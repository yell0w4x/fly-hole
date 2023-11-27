FROM python:3.11-bullseye

RUN apt-get update -y
RUN apt-get install -y iproute2 htop
RUN cd /tmp && wget https://github.com/Yelp/dumb-init/releases/download/v1.2.5/dumb-init_1.2.5_amd64.deb
RUN apt-get install /tmp/dumb-init_1.2.5_amd64.deb

WORKDIR /test
COPY e2e-tests/src/requirements.txt /test/requirements.txt
RUN pip install -r requirements.txt
COPY e2e-tests/src /test/
COPY python /test/sut

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["pytest"]
