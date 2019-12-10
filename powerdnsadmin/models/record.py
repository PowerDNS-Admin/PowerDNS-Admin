import traceback
import itertools
import dns.reversename
import dns.inet
import dns.name
from distutils.version import StrictVersion
from flask import current_app
from urllib.parse import urljoin
from distutils.util import strtobool

from .. import utils
from .base import db
from .setting import Setting
from .domain import Domain
from .domain_setting import DomainSetting


class Record(object):
    """
    This is not a model, it's just an object
    which be assigned data from PowerDNS API
    """
    def __init__(self,
                 name=None,
                 type=None,
                 status=None,
                 ttl=None,
                 data=None,
                 comment_data=None):
        self.name = name
        self.type = type
        self.status = status
        self.ttl = ttl
        self.data = data
        self.comment_data = comment_data
        # PDNS configs
        self.PDNS_STATS_URL = Setting().get('pdns_api_url')
        self.PDNS_API_KEY = Setting().get('pdns_api_key')
        self.PDNS_VERSION = Setting().get('pdns_version')
        self.API_EXTENDED_URL = utils.pdns_api_extended_uri(self.PDNS_VERSION)
        self.PRETTY_IPV6_PTR = Setting().get('pretty_ipv6_ptr')

        if StrictVersion(self.PDNS_VERSION) >= StrictVersion('4.0.0'):
            self.NEW_SCHEMA = True
        else:
            self.NEW_SCHEMA = False

    def get_record_data(self, domain):
        """
        Query domain's DNS records via API
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)),
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     headers=headers)
        except Exception as e:
            current_app.logger.error(
                "Cannot fetch domain's record data from remote powerdns api. DETAIL: {0}"
                .format(e))
            return False

        if self.NEW_SCHEMA:
            rrsets = jdata['rrsets']
            for rrset in rrsets:
                if rrset['records']:
                    r_name = rrset['name'].rstrip('.')
                    if self.PRETTY_IPV6_PTR:  # only if activated
                        if rrset['type'] == 'PTR':  # only ptr
                            if 'ip6.arpa' in r_name:  # only if v6-ptr
                                r_name = dns.reversename.to_address(
                                    dns.name.from_text(r_name))

                    rrset['name'] = r_name
                    rrset['content'] = rrset['records'][0]['content']
                    rrset['disabled'] = rrset['records'][0]['disabled']

                    # Get the record's comment. PDNS support multiple comments
                    # per record. However, we are only interested in the 1st
                    # one, for now.
                    rrset['comment_data'] = {"content": "", "account": ""}
                    if rrset['comments']:
                        rrset['comment_data'] = rrset['comments'][0]
            return {'records': rrsets}

        return jdata

    def add(self, domain):
        """
        Add a record to domain
        """
        # validate record first
        r = self.get_record_data(domain)
        records = r['records']
        check = list(filter(lambda check: check['name'] == self.name, records))
        if check:
            r = check[0]
            if r['type'] in ('A', 'AAAA', 'CNAME'):
                return {
                    'status': 'error',
                    'msg':
                    'Record already exists with type "A", "AAAA" or "CNAME"'
                }

        # continue if the record is ready to be added
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if self.NEW_SCHEMA:
            data = {
                "rrsets": [{
                    "name":
                    self.name.rstrip('.') + '.',
                    "type":
                    self.type,
                    "changetype":
                    "REPLACE",
                    "ttl":
                    self.ttl,
                    "records": [{
                        "content": self.data,
                        "disabled": self.status,
                    }],
                    "comments":
                    [self.comment_data] if self.comment_data else []
                }]
            }
        else:
            data = {
                "rrsets": [{
                    "name":
                    self.name,
                    "type":
                    self.type,
                    "changetype":
                    "REPLACE",
                    "records": [{
                        "content": self.data,
                        "disabled": self.status,
                        "name": self.name,
                        "ttl": self.ttl,
                        "type": self.type
                    }],
                    "comments":
                    [self.comment_data] if self.comment_data else []
                }]
            }

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PATCH',
                                     data=data)
            current_app.logger.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was added successfully'}
        except Exception as e:
            current_app.logger.error(
                "Cannot add record {0}/{1}/{2} to domain {3}. DETAIL: {4}".
                format(self.name, self.type, self.data, domain, e))
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def compare(self, domain_name, new_records):
        """
        Compare new records with current powerdns record data
        Input is a list of hashes (records)
        """
        # get list of current records we have in powerdns
        current_records = self.get_record_data(domain_name)['records']

        # convert them to list of list (just has [name, type]) instead of list of hash
        # to compare easier
        list_current_records = [[x['name'], x['type']]
                                for x in current_records]
        list_new_records = [[x['name'], x['type']] for x in new_records]

        # get list of deleted records
        # they are the records which exist in list_current_records but not in list_new_records
        list_deleted_records = [
            x for x in list_current_records if x not in list_new_records
        ]

        # convert back to list of hash
        deleted_records = [
            x for x in current_records
            if [x['name'], x['type']] in list_deleted_records and (
                x['type'] in Setting().get_records_allow_to_edit()
                and x['type'] != 'SOA')
        ]

        # return a tuple
        return deleted_records, new_records

    def apply(self, domain, post_records):
        """
        Apply record changes to domain
        """
        records = []
        for r in post_records:
            r_name = domain if r['record_name'] in [
                '@', ''
            ] else r['record_name'] + '.' + domain
            r_type = r['record_type']
            if self.PRETTY_IPV6_PTR:  # only if activated
                if self.NEW_SCHEMA:  # only if new schema
                    if r_type == 'PTR':  # only ptr
                        if ':' in r['record_name']:  # dirty ipv6 check
                            r_name = r['record_name']

            r_data = domain if r_type == 'CNAME' and r['record_data'] in [
                '@', ''
            ] else r['record_data']

            record = {
                "name": r_name,
                "type": r_type,
                "content": r_data,
                "disabled":
                True if r['record_status'] == 'Disabled' else False,
                "ttl": int(r['record_ttl']) if r['record_ttl'] else 3600,
                "comment_data": r['comment_data']
            }
            records.append(record)

        deleted_records, new_records = self.compare(domain, records)

        records = []
        for r in deleted_records:
            r_name = r['name'].rstrip(
                '.') + '.' if self.NEW_SCHEMA else r['name']
            r_type = r['type']
            if self.PRETTY_IPV6_PTR:  # only if activated
                if self.NEW_SCHEMA:  # only if new schema
                    if r_type == 'PTR':  # only ptr
                        if ':' in r['name']:  # dirty ipv6 check
                            r_name = dns.reversename.from_address(
                                r['name']).to_text()

            record = {
                "name": r_name,
                "type": r_type,
                "changetype": "DELETE",
                "records": []
            }
            records.append(record)

        postdata_for_delete = {"rrsets": records}

        records = []
        for r in new_records:
            if self.NEW_SCHEMA:
                r_name = r['name'].rstrip('.') + '.'
                r_type = r['type']
                if self.PRETTY_IPV6_PTR:  # only if activated
                    if r_type == 'PTR':  # only ptr
                        if ':' in r['name']:  # dirty ipv6 check
                            r_name = r['name']

                record = {
                    "name":
                    r_name,
                    "type":
                    r_type,
                    "changetype":
                    "REPLACE",
                    "ttl":
                    r['ttl'],
                    "records": [{
                        "content": r['content'],
                        "disabled": r['disabled']
                    }],
                    "comments":
                    r['comment_data']
                }
            else:
                record = {
                    "name":
                    r['name'],
                    "type":
                    r['type'],
                    "changetype":
                    "REPLACE",
                    "records": [{
                        "content": r['content'],
                        "disabled": r['disabled'],
                        "name": r['name'],
                        "ttl": r['ttl'],
                        "type": r['type'],
                        "priority":
                        10,  # priority field for pdns 3.4.1. https://doc.powerdns.com/md/authoritative/upgrading/
                    }],
                    "comments":
                    r['comment_data']
                }

            records.append(record)

        # Adjustment to add multiple records which described in
        # https://github.com/ngoduykhanh/PowerDNS-Admin/issues/5#issuecomment-181637576
        final_records = []
        records = sorted(records,
                         key=lambda item:
                         (item["name"], item["type"], item["changetype"]))
        for key, group in itertools.groupby(
                records, lambda item:
            (item["name"], item["type"], item["changetype"])):
            if self.NEW_SCHEMA:
                r_name = key[0]
                r_type = key[1]
                r_changetype = key[2]

                if self.PRETTY_IPV6_PTR:  # only if activated
                    if r_type == 'PTR':  # only ptr
                        if ':' in r_name:  # dirty ipv6 check
                            r_name = dns.reversename.from_address(
                                r_name).to_text()

                new_record = {
                    "name": r_name,
                    "type": r_type,
                    "changetype": r_changetype,
                    "ttl": None,
                    "records": []
                }
                for item in group:
                    temp_content = item['records'][0]['content']
                    temp_disabled = item['records'][0]['disabled']
                    if key[1] in ['MX', 'CNAME', 'SRV', 'NS']:
                        if temp_content.strip()[-1:] != '.':
                            temp_content += '.'

                    if new_record['ttl'] is None:
                        new_record['ttl'] = item['ttl']
                    new_record['records'].append({
                        "content": temp_content,
                        "disabled": temp_disabled
                    })
                    new_record['comments'] = item['comments']
                final_records.append(new_record)

            else:

                final_records.append({
                    "name":
                    key[0],
                    "type":
                    key[1],
                    "changetype":
                    key[2],
                    "records": [{
                        "content": item['records'][0]['content'],
                        "disabled": item['records'][0]['disabled'],
                        "name": key[0],
                        "ttl": item['records'][0]['ttl'],
                        "type": key[1],
                        "priority": 10,
                    } for item in group]
                })

        postdata_for_new = {"rrsets": final_records}
        current_app.logger.debug(
            "postdata_for_new: {}".format(postdata_for_new))
        current_app.logger.debug(
            "postdata_for_delete: {}".format(postdata_for_delete))
        current_app.logger.info(
            urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)))
        try:
            headers = {}
            headers['X-API-Key'] = self.PDNS_API_KEY
            jdata1 = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)),
                                      headers=headers,
                                      method='PATCH',
                                      data=postdata_for_delete)
            jdata2 = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)),
                                      headers=headers,
                                      timeout=int(
                                          Setting().get('pdns_api_timeout')),
                                      method='PATCH',
                                      data=postdata_for_new)

            if 'error' in jdata1.keys():
                current_app.logger.error('Cannot apply record changes.')
                current_app.logger.debug(jdata1['error'])
                return {'status': 'error', 'msg': jdata1['error']}
            elif 'error' in jdata2.keys():
                current_app.logger.error('Cannot apply record changes.')
                current_app.logger.debug(jdata2['error'])
                return {'status': 'error', 'msg': jdata2['error']}
            else:
                self.auto_ptr(domain, new_records, deleted_records)
                self.update_db_serial(domain)
                current_app.logger.info('Record was applied successfully.')
                return {
                    'status': 'ok',
                    'msg': 'Record was applied successfully'
                }
        except Exception as e:
            current_app.logger.error(
                "Cannot apply record changes to domain {0}. Error: {1}".format(
                    domain, e))
            current_app.logger.debug(traceback.format_exc())
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def auto_ptr(self, domain, new_records, deleted_records):
        """
        Add auto-ptr records
        """
        domain_obj = Domain.query.filter(Domain.name == domain).first()
        domain_auto_ptr = DomainSetting.query.filter(
            DomainSetting.domain == domain_obj).filter(
                DomainSetting.setting == 'auto_ptr').first()
        domain_auto_ptr = strtobool(
            domain_auto_ptr.value) if domain_auto_ptr else False

        system_auto_ptr = Setting().get('auto_ptr')

        if system_auto_ptr or domain_auto_ptr:
            try:
                d = Domain()
                for r in new_records:
                    if r['type'] in ['A', 'AAAA']:
                        r_name = r['name'] + '.'
                        r_content = r['content']
                        reverse_host_address = dns.reversename.from_address(
                            r_content).to_text()
                        domain_reverse_name = d.get_reverse_domain_name(
                            reverse_host_address)
                        d.create_reverse_domain(domain, domain_reverse_name)
                        self.name = dns.reversename.from_address(
                            r_content).to_text().rstrip('.')
                        self.type = 'PTR'
                        self.status = r['disabled']
                        self.ttl = r['ttl']
                        self.data = r_name
                        self.add(domain_reverse_name)
                for r in deleted_records:
                    if r['type'] in ['A', 'AAAA']:
                        r_content = r['content']
                        reverse_host_address = dns.reversename.from_address(
                            r_content).to_text()
                        domain_reverse_name = d.get_reverse_domain_name(
                            reverse_host_address)
                        self.name = reverse_host_address
                        self.type = 'PTR'
                        self.data = r_content
                        self.delete(domain_reverse_name)
                return {
                    'status': 'ok',
                    'msg': 'Auto-PTR record was updated successfully'
                }
            except Exception as e:
                current_app.logger.error(
                    "Cannot update auto-ptr record changes to domain {0}. Error: {1}"
                    .format(domain, e))
                current_app.logger.debug(traceback.format_exc())
                return {
                    'status':
                    'error',
                    'msg':
                    'Auto-PTR creation failed. There was something wrong, please contact administrator.'
                }

    def delete(self, domain):
        """
        Delete a record from domain
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        data = {
            "rrsets": [{
                "name": self.name.rstrip('.') + '.',
                "type": self.type,
                "changetype": "DELETE",
                "records": []
            }]
        }
        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PATCH',
                                     data=data)
            current_app.logger.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was removed successfully'}
        except Exception as e:
            current_app.logger.error(
                "Cannot remove record {0}/{1}/{2} from domain {3}. DETAIL: {4}"
                .format(self.name, self.type, self.data, domain, e))
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def is_allowed_edit(self):
        """
        Check if record is allowed to edit
        """
        return self.type in Setting().get_records_allow_to_edit()

    def is_allowed_delete(self):
        """
        Check if record is allowed to removed
        """
        return (self.type in Setting().get_records_allow_to_edit()
                and self.type != 'SOA')

    def exists(self, domain):
        """
        Check if record is present within domain records, and if it's present set self to found record
        """
        jdata = self.get_record_data(domain)
        jrecords = jdata['records']

        for jr in jrecords:
            if jr['name'] == self.name and jr['type'] == self.type:
                self.name = jr['name']
                self.type = jr['type']
                self.status = jr['disabled']
                self.ttl = jr['ttl']
                self.data = jr['content']
                self.priority = 10
                return True
        return False

    def update(self, domain, content):
        """
        Update single record
        """
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY

        if self.NEW_SCHEMA:
            data = {
                "rrsets": [{
                    "name":
                    self.name + '.',
                    "type":
                    self.type,
                    "ttl":
                    self.ttl,
                    "changetype":
                    "REPLACE",
                    "records": [{
                        "content": content,
                        "disabled": self.status,
                    }]
                }]
            }
        else:
            data = {
                "rrsets": [{
                    "name":
                    self.name,
                    "type":
                    self.type,
                    "changetype":
                    "REPLACE",
                    "records": [{
                        "content": content,
                        "disabled": self.status,
                        "name": self.name,
                        "ttl": self.ttl,
                        "type": self.type,
                        "priority": 10
                    }]
                }]
            }
        try:
            utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(domain)),
                             headers=headers,
                             timeout=int(Setting().get('pdns_api_timeout')),
                             method='PATCH',
                             data=data)
            current_app.logger.debug("dyndns data: {0}".format(data))
            return {'status': 'ok', 'msg': 'Record was updated successfully'}
        except Exception as e:
            current_app.logger.error(
                "Cannot add record {0}/{1}/{2} to domain {3}. DETAIL: {4}".
                format(self.name, self.type, self.data, domain, e))
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def update_db_serial(self, domain):
        headers = {}
        headers['X-API-Key'] = self.PDNS_API_KEY
        jdata = utils.fetch_json(urljoin(
            self.PDNS_STATS_URL, self.API_EXTENDED_URL +
            '/servers/localhost/zones/{0}'.format(domain)),
                                 headers=headers,
                                 timeout=int(
                                     Setting().get('pdns_api_timeout')),
                                 method='GET')
        serial = jdata['serial']

        domain = Domain.query.filter(Domain.name == domain).first()
        if domain:
            domain.serial = serial
            db.session.commit()
            return {
                'status': True,
                'msg': 'Synced local serial for domain name {0}'.format(domain)
            }
        else:
            return {
                'status': False,
                'msg':
                'Could not find domain name {0} in local db'.format(domain)
            }
