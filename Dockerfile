FROM ubuntu:23.10

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends apt-utils 2>/dev/null && \
    apt-get install -y software-properties-common \
    python3.11 \
    python3.11-venv \
    python3-pip 

RUN python3 -m venv /venv

COPY ./requirements.txt /tmp/requirements.txt

COPY . /cisco-ise-dna-monitoring

RUN pip install -r /tmp/requirements.txt --break-system-packages

WORKDIR /cisco-ise-dna-monitoring

CMD ["tail","-f","/dev/null"]