FROM ubuntu:16.04

RUN apt-get update && apt-get install -y --fix-missing \
    gcc mongodb git wkhtmltopdf xvfb python2.7 python-pip \
    python-dev build-essential libssl-dev libffi-dev \
    apache2 libapache2-mod-wsgi; \
    git clone https://github.com/FIWARE-TMForum/business-ecosystem-charging-backend.git; \
    pip install sh

WORKDIR business-ecosystem-charging-backend

RUN git checkout develop; \
    mkdir -p /data/db/; \
    mkdir ./src/media; \
    mkdir ./src/media/bills; \
    mkdir ./src/media/assets; \
    mkdir ./src/plugins

ENV WORKSPACE=`pwd`

RUN ./python-dep-install.sh

# Create volumes
VOLUME /data/db
VOLUME /business-ecosystem-charging-backend/src/media/bills
VOLUME /business-ecosystem-charging-backend/src/media/assets
VOLUME /business-ecosystem-charging-backend/src/plugins

WORKDIR src

RUN rm wsgi.py
COPY wsgi.py .

WORKDIR /etc/apache2/
COPY charging.conf ./sites-available

RUN ln -s ../sites-available/charging.conf ./sites-enabled/charging.conf; \
    sed -i "s|Listen 80|Listen 8006|g" ports.conf

WORKDIR /business-ecosystem-charging-backend/src

COPY ./entrypoint.sh /

EXPOSE 8006

ENTRYPOINT ["/entrypoint.sh"]

