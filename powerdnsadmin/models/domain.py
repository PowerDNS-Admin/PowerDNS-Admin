import re
import traceback
from flask import current_app
from urllib.parse import urljoin
from distutils.util import strtobool

from ..lib import utils
from .base import db, domain_apikey
from .setting import Setting
from .user import User
from .account import Account
from .account import AccountUser
from .domain_user import DomainUser
from .domain_setting import DomainSetting
from .history import History


class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True, unique=True)
    master = db.Column(db.String(128))
    type = db.Column(db.String(6), nullable=False)
    serial = db.Column(db.BigInteger)
    notified_serial = db.Column(db.BigInteger)
    last_check = db.Column(db.Integer)
    dnssec = db.Column(db.Integer)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    account = db.relationship("Account", back_populates="domains")
    settings = db.relationship('DomainSetting', back_populates='domain')
    apikeys = db.relationship("ApiKey",
                              secondary=domain_apikey,
                              back_populates="domains")

    def __init__(self,
                 id=None,
                 name=None,
                 master=None,
                 type='NATIVE',
                 serial=None,
                 notified_serial=None,
                 last_check=None,
                 dnssec=None,
                 account_id=None):
        self.id = id
        self.name = name
        self.master = master
        self.type = type
        self.serial = serial
        self.notified_serial = notified_serial
        self.last_check = last_check
        self.dnssec = dnssec
        self.account_id = account_id
        # PDNS configs
        self.PDNS_STATS_URL = Setting().get('pdns_api_url')
        self.PDNS_API_KEY = Setting().get('pdns_api_key')
        self.PDNS_VERSION = Setting().get('pdns_version')
        self.API_EXTENDED_URL = utils.pdns_api_extended_uri(self.PDNS_VERSION)

    def __repr__(self):
        return '<Domain {0}>'.format(self.name)

    def add_setting(self, setting, value):
        try:
            self.settings.append(DomainSetting(setting=setting, value=value))
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(
                'Can not create setting {0} for domain {1}. {2}'.format(
                    setting, self.name, e))
            return False

    def get_domain_info(self, domain_name):
        """
        Get all domains which has in PowerDNS
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        jdata = utils.fetch_json(urljoin(
            self.PDNS_STATS_URL, self.API_EXTENDED_URL +
            '/servers/localhost/zones/{0}'.format(domain_name)),
                                 headers=headers,
                                 timeout=int(
                                     Setting().get('pdns_api_timeout')),
                                 verify=Setting().get('verify_ssl_connections'))
        return jdata

    def get_domains(self):
        """
        Get all domains which has in PowerDNS
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        jdata = utils.fetch_json(
            urljoin(self.PDNS_STATS_URL,
                    self.API_EXTENDED_URL + '/servers/localhost/zones'),
            headers=headers,
            timeout=int(Setting().get('pdns_api_timeout')),
            verify=Setting().get('verify_ssl_connections'))
        return jdata

    def get_id_by_name(self, name):
        """
        Return domain id
        """
        try:
            domain = Domain.query.filter(Domain.name == name).first()
            return domain.id
        except Exception as e:
            current_app.logger.error(
                'Domain does not exist. ERROR: {0}'.format(e))
            return None

    def update(self):
        """
        Fetch zones (domains) from PowerDNS and update into DB
        """
        db_domain = Domain.query.all()
        list_db_domain = [d.name for d in db_domain]
        dict_db_domain = dict((x.name, x) for x in db_domain)
        current_app.logger.info("Found {} entries in PowerDNS-Admin".format(
            len(list_db_domain)))
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL,
                        self.API_EXTENDED_URL + '/servers/localhost/zones'),
                headers=headers,
                timeout=int(Setting().get('pdns_api_timeout')),
                verify=Setting().get('verify_ssl_connections'))
            list_jdomain = [d['name'].rstrip('.') for d in jdata]
            current_app.logger.info(
                "Found {} entries in PowerDNS server".format(len(list_jdomain)))

            try:
                # domains should remove from db since it doesn't exist in powerdns anymore
                should_removed_db_domain = list(
                    set(list_db_domain).difference(list_jdomain))
                for domain_name in should_removed_db_domain:
                    self.delete_domain_from_pdnsadmin(domain_name, do_commit=False)
            except Exception as e:
                current_app.logger.error(
                    'Can not delete domain from DB. DETAIL: {0}'.format(e))
                current_app.logger.debug(traceback.format_exc())

            # update/add new domain
            for data in jdata:
                if 'account' in data:
                    account_id = Account().get_id_by_name(data['account'])
                else:
                    current_app.logger.debug(
                        "No 'account' data found in API result - Unsupported PowerDNS version?"
                    )
                    account_id = None
                domain = dict_db_domain.get(data['name'].rstrip('.'), None)
                if domain:
                    self.update_pdns_admin_domain(domain, account_id, data, do_commit=False)
                else:
                    # add new domain
                    self.add_domain_to_powerdns_admin(domain=data, do_commit=False)

            db.session.commit()
            current_app.logger.info('Update domain finished')
            return {
                'status': 'ok',
                'msg': 'Domain table has been updated successfully'
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Can not update domain table. Error: {0}'.format(e))
            return {'status': 'error', 'msg': 'Can not update domain table'}

    def update_pdns_admin_domain(self, domain, account_id, data, do_commit=True):
        # existing domain, only update if something actually has changed
        if (domain.master != str(data['masters'])
                or domain.type != data['kind']
                or domain.serial != data['serial']
                or domain.notified_serial != data['notified_serial']
                or domain.last_check != (1 if data['last_check'] else 0)
                or domain.dnssec != data['dnssec']
                or domain.account_id != account_id):

            domain.master = str(data['masters'])
            domain.type = data['kind']
            domain.serial = data['serial']
            domain.notified_serial = data['notified_serial']
            domain.last_check = 1 if data['last_check'] else 0
            domain.dnssec = 1 if data['dnssec'] else 0
            domain.account_id = account_id
            try:
                if do_commit:
                    db.session.commit()
                current_app.logger.info("Updated PDNS-Admin domain {0}".format(
                    domain.name))
            except Exception as e:
                db.session.rollback()
                current_app.logger.info("Rolled back Domain {0} {1}".format(
                    domain.name, e))
                raise

    def add(self,
            domain_name,
            domain_type,
            soa_edit_api,
            domain_ns=[],
            domain_master_ips=[],
            account_name=None):
        """
        Add a domain to power dns
        """

        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        domain_name = domain_name + '.'
        domain_ns = [ns + '.' for ns in domain_ns]

        if soa_edit_api not in ["DEFAULT", "INCREASE", "EPOCH", "OFF"]:
            soa_edit_api = 'DEFAULT'

        elif soa_edit_api == 'OFF':
            soa_edit_api = ''

        post_data = {
            "name": domain_name,
            "kind": domain_type,
            "masters": domain_master_ips,
            "nameservers": domain_ns,
            "soa_edit_api": soa_edit_api,
            "account": account_name
        }

        try:
            jdata = utils.fetch_json(
                urljoin(self.PDNS_STATS_URL,
                        self.API_EXTENDED_URL + '/servers/localhost/zones'),
                headers=headers,
                timeout=int(Setting().get('pdns_api_timeout')),
                method='POST',
                verify=Setting().get('verify_ssl_connections'),
                data=post_data)
            if 'error' in jdata.keys():
                current_app.logger.error(jdata['error'])
                if jdata.get('http_code') == 409:
                    return {'status': 'error', 'msg': 'Domain already exists'}
                return {'status': 'error', 'msg': jdata['error']}
            else:
                current_app.logger.info(
                    'Added domain successfully to PowerDNS: {0}'.format(
                        domain_name))
                self.add_domain_to_powerdns_admin(domain_dict=post_data)
                return {'status': 'ok', 'msg': 'Added domain successfully'}
        except Exception as e:
            current_app.logger.error('Cannot add domain {0} {1}'.format(
                domain_name, e))
            current_app.logger.debug(traceback.format_exc())
            return {'status': 'error', 'msg': 'Cannot add this domain.'}

    def add_domain_to_powerdns_admin(self, domain=None, domain_dict=None, do_commit=True):
        """
        Read Domain from PowerDNS and add into PDNS-Admin
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        if not domain:
            try:
                domain = utils.fetch_json(
                    urljoin(
                        self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                        '/servers/localhost/zones/{0}'.format(
                            domain_dict['name'])),
                    headers=headers,
                    timeout=int(Setting().get('pdns_api_timeout')),
                    verify=Setting().get('verify_ssl_connections'))
            except Exception as e:
                current_app.logger.error('Can not read domain from PDNS')
                current_app.logger.error(e)
                current_app.logger.debug(traceback.format_exc())

        if 'account' in domain:
            account_id = Account().get_id_by_name(domain['account'])
        else:
            current_app.logger.debug(
                "No 'account' data found in API result - Unsupported PowerDNS version?"
            )
            account_id = None
        # add new domain
        d = Domain()
        d.name = domain['name'].rstrip('.')  # lgtm [py/modification-of-default-value]
        d.master = str(domain['masters'])
        d.type = domain['kind']
        d.serial = domain['serial']
        d.notified_serial = domain['notified_serial']
        d.last_check = domain['last_check']
        d.dnssec = 1 if domain['dnssec'] else 0
        d.account_id = account_id
        db.session.add(d)
        try:
            if do_commit:
                db.session.commit()
            current_app.logger.info(
                "Synced PowerDNS Domain to PDNS-Admin: {0}".format(d.name))
            return {
                'status': 'ok',
                'msg': 'Added Domain successfully to PowerDNS-Admin'
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.info("Rolled back Domain {0}".format(d.name))
            raise

    def update_soa_setting(self, domain_name, soa_edit_api):
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return {'status': 'error', 'msg': 'Domain does not exist.'}
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if soa_edit_api not in ["DEFAULT", "INCREASE", "EPOCH", "OFF"]:
            soa_edit_api = 'DEFAULT'

        elif soa_edit_api == 'OFF':
            soa_edit_api = ''

        post_data = {"soa_edit_api": soa_edit_api, "kind": domain.type}

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain.name)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PUT',
                                     verify=Setting().get('verify_ssl_connections'),
                                     data=post_data)
            if 'error' in jdata.keys():
                current_app.logger.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                current_app.logger.info(
                    'soa-edit-api changed for domain {0} successfully'.format(
                        domain_name))
                return {
                    'status': 'ok',
                    'msg': 'soa-edit-api changed successfully'
                }
        except Exception as e:
            current_app.logger.debug(e)
            current_app.logger.debug(traceback.format_exc())
            current_app.logger.error(
                'Cannot change soa-edit-api for domain {0}'.format(
                    domain_name))
            return {
                'status': 'error',
                'msg': 'Cannot change soa-edit-api for this domain.'
            }

    def update_kind(self, domain_name, kind, masters=[]):
        """
        Update zone kind: Native / Master / Slave
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return {'status': 'error', 'msg': 'Domain does not exist.'}
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        post_data = {"kind": kind, "masters": masters}

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain.name)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PUT',
                                     verify=Setting().get('verify_ssl_connections'),
                                     data=post_data)
            if 'error' in jdata.keys():
                current_app.logger.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                current_app.logger.info(
                    'Update domain kind for {0} successfully'.format(
                        domain_name))
                return {
                    'status': 'ok',
                    'msg': 'Domain kind changed successfully'
                }
        except Exception as e:
            current_app.logger.error(
                'Cannot update kind for domain {0}. Error: {1}'.format(
                    domain_name, e))
            current_app.logger.debug(traceback.format_exc())

            return {
                'status': 'error',
                'msg': 'Cannot update kind for this domain.'
            }

    def create_reverse_domain(self, domain_name, domain_reverse_name):
        """
        Check the existing reverse lookup domain,
        if not exists create a new one automatically
        """
        domain_obj = Domain.query.filter(Domain.name == domain_name).first()
        domain_auto_ptr = DomainSetting.query.filter(
            DomainSetting.domain == domain_obj).filter(
                DomainSetting.setting == 'auto_ptr').first()
        domain_auto_ptr = strtobool(
            domain_auto_ptr.value) if domain_auto_ptr else False
        system_auto_ptr = Setting().get('auto_ptr')
        self.name = domain_name
        domain_id = self.get_id_by_name(domain_reverse_name)
        if None == domain_id and \
            (
                system_auto_ptr or
                domain_auto_ptr
            ):
            result = self.add(domain_reverse_name, 'Master', 'DEFAULT', '', '')
            self.update()
            if result['status'] == 'ok':
                history = History(msg='Add reverse lookup domain {0}'.format(
                    domain_reverse_name),
                                  detail=str({
                                      'domain_type': 'Master',
                                      'domain_master_ips': ''
                                  }),
                                  created_by='System')
                history.add()
            else:
                return {
                    'status': 'error',
                    'msg': 'Adding reverse lookup domain failed'
                }
            domain_user_ids = self.get_user()
            if len(domain_user_ids) > 0:
                self.name = domain_reverse_name
                self.grant_privileges(domain_user_ids)
                return {
                    'status':
                    'ok',
                    'msg':
                    'New reverse lookup domain created with granted privileges'
                }
            return {
                'status': 'ok',
                'msg': 'New reverse lookup domain created without users'
            }
        return {'status': 'ok', 'msg': 'Reverse lookup domain already exists'}

    def get_reverse_domain_name(self, reverse_host_address):
        c = 1
        if re.search('ip6.arpa', reverse_host_address):
            for i in range(1, 32, 1):
                address = re.search(
                    '((([a-f0-9]\.){' + str(i) + '})(?P<ipname>.+6.arpa)\.?)',
                    reverse_host_address)
                if None != self.get_id_by_name(address.group('ipname')):
                    c = i
                    break
            return re.search(
                '((([a-f0-9]\.){' + str(c) + '})(?P<ipname>.+6.arpa)\.?)',
                reverse_host_address).group('ipname')
        else:
            for i in range(1, 4, 1):
                address = re.search(
                    '((([0-9]+\.){' + str(i) + '})(?P<ipname>.+r.arpa)\.?)',
                    reverse_host_address)
                if None != self.get_id_by_name(address.group('ipname')):
                    c = i
                    break
            return re.search(
                '((([0-9]+\.){' + str(c) + '})(?P<ipname>.+r.arpa)\.?)',
                reverse_host_address).group('ipname')

    def delete(self, domain_name):
        """
        Delete a single domain name from powerdns
        """
        try:
            self.delete_domain_from_powerdns(domain_name)
            self.delete_domain_from_pdnsadmin(domain_name)
            return {'status': 'ok', 'msg': 'Delete domain successfully'}
        except Exception as e:
            current_app.logger.error(
                'Cannot delete domain {0}'.format(domain_name))
            current_app.logger.error(e)
            current_app.logger.debug(traceback.format_exc())
            return {'status': 'error', 'msg': 'Cannot delete domain'}

    def delete_domain_from_powerdns(self, domain_name):
        """
        Delete a single domain name from powerdns
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        utils.fetch_json(urljoin(
            self.PDNS_STATS_URL, self.API_EXTENDED_URL +
            '/servers/localhost/zones/{0}'.format(domain_name)),
                         headers=headers,
                         timeout=int(Setting().get('pdns_api_timeout')),
                         method='DELETE',
                         verify=Setting().get('verify_ssl_connections'))
        current_app.logger.info(
            'Deleted domain successfully from PowerDNS: {0}'.format(
                domain_name))
        return {'status': 'ok', 'msg': 'Delete domain successfully'}

    def delete_domain_from_pdnsadmin(self, domain_name, do_commit=True):
        # Revoke permission before deleting domain
        domain = Domain.query.filter(Domain.name == domain_name).first()
        domain_user = DomainUser.query.filter(
            DomainUser.domain_id == domain.id)
        if domain_user:
            domain_user.delete()
        domain_setting = DomainSetting.query.filter(
            DomainSetting.domain_id == domain.id)
        if domain_setting:
            domain_setting.delete()
        domain.apikeys[:] = []

        # then remove domain
        Domain.query.filter(Domain.name == domain_name).delete()
        if do_commit:
            db.session.commit()
        current_app.logger.info(
            "Deleted domain successfully from pdnsADMIN: {}".format(
                domain_name))

    def get_user(self):
        """
        Get users (id) who have access to this domain name
        """
        user_ids = []
        query = db.session.query(
            DomainUser, Domain).filter(User.id == DomainUser.user_id).filter(
                Domain.id == DomainUser.domain_id).filter(
                    Domain.name == self.name).all()
        for q in query:
            user_ids.append(q[0].user_id)
        return user_ids

    def grant_privileges(self, new_user_ids):
        """
        Reconfigure domain_user table
        """

        domain_id = self.get_id_by_name(self.name)
        domain_user_ids = self.get_user()

        removed_ids = list(set(domain_user_ids).difference(new_user_ids))
        added_ids = list(set(new_user_ids).difference(domain_user_ids))

        try:
            for uid in removed_ids:
                DomainUser.query.filter(DomainUser.user_id == uid).filter(
                    DomainUser.domain_id == domain_id).delete()
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot revoke user privileges on domain {0}. DETAIL: {1}'.
                format(self.name, e))
            current_app.logger.debug(print(traceback.format_exc()))

        try:
            for uid in added_ids:
                du = DomainUser(domain_id, uid)
                db.session.add(du)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                'Cannot grant user privileges to domain {0}. DETAIL: {1}'.
                format(self.name, e))
            current_app.logger.debug(print(traceback.format_exc()))

    def update_from_master(self, domain_name):
        """
        Update records from Master DNS server
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                r = utils.fetch_json(urljoin(
                    self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                    '/servers/localhost/zones/{0}/axfr-retrieve'.format(
                        domain.name)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PUT',
                                     verify=Setting().get('verify_ssl_connections'))
                return {'status': 'ok', 'msg': r.get('result')}
            except Exception as e:
                current_app.logger.error(
                    'Cannot update from master. DETAIL: {0}'.format(e))
                return {
                    'status':
                    'error',
                    'msg':
                    'There was something wrong, please contact administrator'
                }
        else:
            return {'status': 'error', 'msg': 'This domain does not exist'}

    def get_domain_dnssec(self, domain_name):
        """
        Get domain DNSSEC information
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                jdata = utils.fetch_json(
                    urljoin(
                        self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                        '/servers/localhost/zones/{0}/cryptokeys'.format(
                            domain.name)),
                    headers=headers,
                    timeout=int(Setting().get('pdns_api_timeout')),
                    method='GET',
                    verify=Setting().get('verify_ssl_connections'))
                if 'error' in jdata:
                    return {
                        'status': 'error',
                        'msg': 'DNSSEC is not enabled for this domain'
                    }
                else:
                    return {'status': 'ok', 'dnssec': jdata}
            except Exception as e:
                current_app.logger.error(
                    'Cannot get domain dnssec. DETAIL: {0}'.format(e))
                return {
                    'status':
                    'error',
                    'msg':
                    'There was something wrong, please contact administrator'
                }
        else:
            return {'status': 'error', 'msg': 'This domain does not exist'}

    def enable_domain_dnssec(self, domain_name):
        """
        Enable domain DNSSEC
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                # Enable API-RECTIFY for domain, BEFORE activating DNSSEC
                post_data = {"api_rectify": True}
                jdata = utils.fetch_json(
                    urljoin(
                        self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                        '/servers/localhost/zones/{0}'.format(domain.name)),
                    headers=headers,
                    timeout=int(Setting().get('pdns_api_timeout')),
                    method='PUT',
                    verify=Setting().get('verify_ssl_connections'),
                    data=post_data)
                if 'error' in jdata:
                    return {
                        'status': 'error',
                        'msg':
                        'API-RECTIFY could not be enabled for this domain',
                        'jdata': jdata
                    }

                # Activate DNSSEC
                post_data = {"keytype": "ksk", "active": True}
                jdata = utils.fetch_json(
                    urljoin(
                        self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                        '/servers/localhost/zones/{0}/cryptokeys'.format(
                            domain.name)),
                    headers=headers,
                    timeout=int(Setting().get('pdns_api_timeout')),
                    method='POST',
                    verify=Setting().get('verify_ssl_connections'),
                    data=post_data)
                if 'error' in jdata:
                    return {
                        'status':
                        'error',
                        'msg':
                        'Cannot enable DNSSEC for this domain. Error: {0}'.
                        format(jdata['error']),
                        'jdata':
                        jdata
                    }

                return {'status': 'ok'}

            except Exception as e:
                current_app.logger.error(
                    'Cannot enable dns sec. DETAIL: {}'.format(e))
                current_app.logger.debug(traceback.format_exc())
                return {
                    'status':
                    'error',
                    'msg':
                    'There was something wrong, please contact administrator'
                }

        else:
            return {'status': 'error', 'msg': 'This domain does not exist'}

    def delete_dnssec_key(self, domain_name, key_id):
        """
        Remove keys DNSSEC
        """
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if domain:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            try:
                # Deactivate DNSSEC
                jdata = utils.fetch_json(
                    urljoin(
                        self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                        '/servers/localhost/zones/{0}/cryptokeys/{1}'.format(
                            domain.name, key_id)),
                    headers=headers,
                    timeout=int(Setting().get('pdns_api_timeout')),
                    method='DELETE',
                    verify=Setting().get('verify_ssl_connections'))
                if jdata != True:
                    return {
                        'status':
                        'error',
                        'msg':
                        'Cannot disable DNSSEC for this domain. Error: {0}'.
                        format(jdata['error']),
                        'jdata':
                        jdata
                    }

                # Disable API-RECTIFY for domain, AFTER deactivating DNSSEC
                post_data = {"api_rectify": False}
                jdata = utils.fetch_json(
                    urljoin(
                        self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                        '/servers/localhost/zones/{0}'.format(domain.name)),
                    headers=headers,
                    timeout=int(Setting().get('pdns_api_timeout')),
                    method='PUT',
                    verify=Setting().get('verify_ssl_connections'),
                    data=post_data)
                if 'error' in jdata:
                    return {
                        'status': 'error',
                        'msg':
                        'API-RECTIFY could not be disabled for this domain',
                        'jdata': jdata
                    }

                return {'status': 'ok'}

            except Exception as e:
                current_app.logger.error(
                    'Cannot delete dnssec key. DETAIL: {0}'.format(e))
                current_app.logger.debug(traceback.format_exc())
                return {
                    'status': 'error',
                    'msg':
                    'There was something wrong, please contact administrator',
                    'domain': domain.name,
                    'id': key_id
                }

        else:
            return {'status': 'error', 'msg': 'This domain does not exist'}

    def assoc_account(self, account_id):
        """
        Associate domain with a domain, specified by account id
        """
        domain_name = self.name

        # Sanity check - domain name
        if domain_name == "":
            return {'status': False, 'msg': 'No domain name specified'}

        # read domain and check that it exists
        domain = Domain.query.filter(Domain.name == domain_name).first()
        if not domain:
            return {'status': False, 'msg': 'Domain does not exist'}

        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        account_name = Account().get_name_by_id(account_id)

        post_data = {"account": account_name}

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain_name)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PUT',
                                     verify=Setting().get('verify_ssl_connections'),
                                     data=post_data)

            if 'error' in jdata.keys():
                current_app.logger.error(jdata['error'])
                return {'status': 'error', 'msg': jdata['error']}
            else:
                self.update()
                msg_str = 'Account changed for domain {0} successfully'
                current_app.logger.info(msg_str.format(domain_name))
                return {'status': 'ok', 'msg': 'account changed successfully'}

        except Exception as e:
            current_app.logger.debug(e)
            current_app.logger.debug(traceback.format_exc())
            msg_str = 'Cannot change account for domain {0}'
            current_app.logger.error(msg_str.format(domain_name))
            return {
                'status': 'error',
                'msg': 'Cannot change account for this domain.'
            }

    def get_account(self):
        """
        Get current account associated with this domain
        """
        domain = Domain.query.filter(Domain.name == self.name).first()

        return domain.account

    def is_valid_access(self, user_id):
        """
        Check if the user is allowed to access this
        domain name
        """
        return db.session.query(Domain) \
            .outerjoin(DomainUser, Domain.id == DomainUser.domain_id) \
            .outerjoin(Account, Domain.account_id == Account.id) \
            .outerjoin(AccountUser, Account.id == AccountUser.account_id) \
            .filter(
                db.or_(
                    DomainUser.user_id == user_id,
                    AccountUser.user_id == user_id
                )).filter(Domain.id == self.id).first()
