FROM python:3.5

RUN mkdir -p /usr/src/app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libav-tools \
    libopus-dev \
  && rm -rf /var/lib/apt/lists/*

COPY . /usr/src/app
RUN /usr/src/app/Install.sh
CMD /usr/src/app/Start.sh
