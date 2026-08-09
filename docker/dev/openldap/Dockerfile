FROM alpine:3.21

RUN apk add --no-cache \
        openldap \
        openldap-back-mdb \
        openldap-clients \
        openldap-overlay-memberof \
        openldap-overlay-refint \
    && mkdir -p /var/lib/openldap/openldap-data /run/openldap \
    && chown -R ldap:ldap /var/lib/openldap /run/openldap

COPY slapd.conf /etc/openldap/slapd.conf
COPY bootstrap-base.ldif /bootstrap-base.ldif
COPY bootstrap-groups.ldif /bootstrap-groups.ldif
COPY entrypoint.sh /entrypoint.sh

RUN chmod 644 /etc/openldap/slapd.conf \
    && chmod 755 /entrypoint.sh \
    && chown ldap:ldap /etc/openldap/slapd.conf

EXPOSE 389

ENTRYPOINT ["/entrypoint.sh"]
