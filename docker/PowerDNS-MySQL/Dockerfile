# PowerDNS Authoritative Server with MySQL backend
# https://www.powerdns.com
#
# The PowerDNS Authoritative Server is the only solution that enables
# authoritative DNS service from all major databases, including but not limited
# to MySQL, PostgreSQL, SQLite3, Oracle, Sybase, Microsoft SQL Server, LDAP and
# plain text files.

FROM winggundamth/ubuntu-base:trusty
MAINTAINER Jirayut Nimsaeng <w [at] winginfotech.net>
ENV FROM_BASE=trusty-20160503.1

# 1) Add PowerDNS repository https://repo.powerdns.com
# 2) Install PowerDNS server
# 3) Clean to reduce Docker image size
ARG APT_CACHER_NG
COPY build-files /build-files
RUN [ -n "$APT_CACHER_NG" ] && \
      echo "Acquire::http::Proxy \"$APT_CACHER_NG\";" \
      > /etc/apt/apt.conf.d/11proxy || true; \
    apt-get update && \
    apt-get install -y curl && \
    curl https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - && \
    echo 'deb [arch=amd64] http://repo.powerdns.com/ubuntu trusty-auth-40 main' \
      > /etc/apt/sources.list.d/pdns-$(lsb_release -cs).list && \
    mv /build-files/pdns-pin /etc/apt/preferences.d/pdns && \
    apt-get update && \
    apt-get install -y pdns-server pdns-backend-mysql mysql-client && \
    mv /build-files/pdns.mysql.conf /etc/powerdns/pdns.d/pdns.mysql.conf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /etc/apt/apt.conf.d/11proxy /build-files \
      /etc/powerdns/pdns.d/pdns.simplebind.conf

# 1) Copy Docker entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh

EXPOSE 53/udp 53 8081
VOLUME ["/var/log", "/etc/powerdns"]
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/sbin/pdns_server", "--guardian=yes"]
