FROM python:3-buster

RUN apt update && apt install -y \
   procps \
   postgresql-client \
   wget \
   gnupg \
   rsync

WORKDIR /tmp/

RUN wget -qO - https://apt.stellar.org/SDF.asc | apt-key add -
RUN echo "deb https://apt.stellar.org/public stable/" | tee -a /etc/apt/sources.list.d/SDF.list
ARG core_version
RUN apt-get update && apt-get install -y     stellar-core=${core_version}

ADD test/wait-for-it.sh /tmp/
ADD test/runtests.sh /tmp/

ADD src/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

ADD src /code/
ADD templates /templates/

WORKDIR /code/
