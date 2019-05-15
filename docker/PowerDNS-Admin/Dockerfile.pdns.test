FROM ubuntu:latest

RUN apt-get update && apt-get install -y pdns-backend-sqlite3 pdns-server sqlite3

COPY ./docker/PowerDNS-Admin/pdns.sqlite.sql /data/pdns.sql
ADD ./docker/PowerDNS-Admin/start.sh /data/

RUN rm -f /etc/powerdns/pdns.d/pdns.simplebind.conf
RUN rm -f /etc/powerdns/pdns.d/bind.conf

RUN chmod +x /data/start.sh && mkdir -p /var/empty/var/run

CMD /data/start.sh
