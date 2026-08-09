#!/bin/sh
set -eu

DATA_DIR=/var/lib/openldap/openldap-data
MARKER="${DATA_DIR}/.bootstrap-complete"
SLAPD_CONF=/etc/openldap/slapd.conf
ADMIN_BIND="cn=admin,dc=example,dc=org"
ADMIN_PW="DevPassword123!"

mkdir -p /run/openldap
chown -R ldap:ldap /var/lib/openldap /run/openldap

wait_for_ldap() {
    for _ in $(seq 1 30); do
        if ldapsearch -x -H ldap://127.0.0.1:389 \
            -D "${ADMIN_BIND}" -w "${ADMIN_PW}" \
            -b dc=example,dc=org -s base '(objectClass=*)' dn \
            >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    echo "OpenLDAP did not become ready during bootstrap" >&2
    return 1
}

if [ ! -f "${MARKER}" ]; then
    echo "Bootstrapping OpenLDAP directory data"
    rm -rf "${DATA_DIR:?}/"*
    # slapadd bypasses overlays, so load people first, then add groups through
    # a temporary slapd so memberOf is maintained by the memberof overlay.
    slapadd -f "${SLAPD_CONF}" -l /bootstrap-base.ldif
    chown -R ldap:ldap "${DATA_DIR}"

    slapd -f "${SLAPD_CONF}" -h "ldap://127.0.0.1/" -u ldap -g ldap
    wait_for_ldap
    ldapadd -x -H ldap://127.0.0.1:389 \
        -D "${ADMIN_BIND}" -w "${ADMIN_PW}" \
        -f /bootstrap-groups.ldif
    kill "$(cat /run/openldap/slapd.pid)"
    # Wait until the temporary slapd exits before replacing it.
    for _ in $(seq 1 30); do
        if [ ! -f /run/openldap/slapd.pid ]; then
            break
        fi
        sleep 1
    done

    touch "${MARKER}"
    chown ldap:ldap "${MARKER}"
fi

exec slapd -f "${SLAPD_CONF}" -h "ldap:///" -u ldap -g ldap -d stats
