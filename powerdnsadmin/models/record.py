import re
import traceback
import dns.reversename
import dns.inet
import dns.name
from flask import current_app
from urllib.parse import urljoin,quote_plus
from distutils.util import strtobool
from itertools import groupby

from .. import utils
from .base import db
from .setting import Setting
from .domain import Domain
from .domain_setting import DomainSetting


def by_record_content_pair(e):
    return e[0]['content']


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

    def get_rrsets(self, domain):
        """
        Query zone's rrsets via PDNS API
        """
        headers = {'X-API-Key': self.PDNS_API_KEY}
        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(quote_plus(domain))),
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     headers=headers,
                                     verify=Setting().get('verify_ssl_connections'))
        except Exception as e:
            current_app.logger.error(
                "Cannot fetch zone's record data from remote powerdns api. DETAIL: {0}"
                .format(e))
            return []

        rrsets=[]
        for r in jdata['rrsets']:
            if len(r['records']) == 0:
                continue

            while len(r['comments'])<len(r['records']):
                r['comments'].append({"content": "", "account": ""})
            r['records'], r['comments'] = (list(t) for t in zip(*sorted(zip(r['records'], r['comments']), key=by_record_content_pair)))
            rrsets.append(r)

        return rrsets

    def add(self, domain_name, rrset):
        """
        Add a record to a zone (Used by auto_ptr and DynDNS)

        Args:
            domain_name(str): The zone name
            rrset(dict): The record in PDNS rrset format

        Returns:
            (dict): A dict contains status code and message
        """
        # Validate record first
        rrsets = self.get_rrsets(domain_name)
        check = list(filter(lambda check: check['name'] == self.name, rrsets))
        if check:
            r = check[0]
            if r['type'] in ('A', 'AAAA', 'CNAME'):
                return {
                    'status': 'error',
                    'msg':
                    'Record already exists with type "A", "AAAA" or "CNAME"'
                }

        # Continue if the record is ready to be added
        headers = {'X-API-Key': self.PDNS_API_KEY, 'Content-Type': 'application/json'}

        try:
            jdata = utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(quote_plus(domain_name))),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PATCH',
                                     verify=Setting().get('verify_ssl_connections'),
                                     data=rrset)
            current_app.logger.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was added successfully'}
        except Exception as e:
            current_app.logger.error(
                "Cannot add record to zone {}. Error: {}".format(
                    domain_name, e))
            current_app.logger.debug("Submitted record rrset: \n{}".format(
                utils.pretty_json(rrset)))
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def merge_rrsets(self, rrsets):
        """
        Merge the rrsets that has same "name" and
        "type".
        Return: a new rrset which has multiple "records"
        and "comments"
        """
        if not rrsets:
            raise Exception("Empty rrsets to merge")
        elif len(rrsets) == 1:
            # It is unique rrset already
            return rrsets[0]
        else:
            # Merge rrsets into one
            rrset = rrsets[0]
            for r in rrsets[1:]:
                rrset['records'] = rrset['records'] + r['records']
                rrset['comments'] = rrset['comments'] + r['comments']
            while len(rrset['comments']) < len(rrset['records']):
                rrset['comments'].append({"content": "", "account": ""})
            zipped_list = zip(rrset['records'], rrset['comments'])
            tuples = zip(*sorted(zipped_list, key=by_record_content_pair))
            rrset['records'], rrset['comments'] = [list(t) for t in tuples]
            return rrset

    def build_rrsets(self, domain_name, submitted_records):
        """
        Build rrsets from the datatable's records

        Args:
            domain_name(str): The zone name
            submitted_records(list): List of records submitted from PDA datatable

        Returns:
            transformed_rrsets(list): List of rrsets converted from PDA datatable
        """
        rrsets = []
        for record in submitted_records:
            # Format the record name
            #
            # Translate template placeholders into proper record data
            record['record_data'] = record['record_data'].replace('[ZONE]', domain_name)
            # Translate record name into punycode (IDN) as that's the only way
            # to convey non-ascii records to the dns server
            record['record_name'] = utils.to_idna(record["record_name"], "encode")
            #TODO: error handling
            # If the record is an alias (CNAME), we will also make sure that
            # the target zone is properly converted to punycode (IDN)
            if record['record_type'] == 'CNAME' or record['record_type'] == 'SOA':
                record['record_data'] = utils.to_idna(record['record_data'], 'encode')
                #TODO: error handling
            # If it is ipv6 reverse zone and PRETTY_IPV6_PTR is enabled,
            # We convert ipv6 address back to reverse record format
            # before submitting to PDNS API.
            if self.PRETTY_IPV6_PTR and re.search(
                    r'ip6\.arpa', domain_name
            ) and record['record_type'] == 'PTR' and ':' in record[
                    'record_name']:
                record_name = dns.reversename.from_address(
                    record['record_name']).to_text()
            # Else, it is forward zone, then record name should be
            # in format "<name>.<domain>.". If it is root
            # domain name (name == '@' or ''), the name should
            # be in format "<domain>."
            else:
                record_name = "{}.{}.".format(
                    record["record_name"],
                    domain_name) if record["record_name"] not in [
                        '@', ''
                    ] else domain_name + '.'

            # Format the record content, it musts end
            # with a dot character if in following types
            if record["record_type"] in [
                    'MX', 'CNAME', 'SRV', 'NS', 'PTR'
            ] and record["record_data"].strip()[-1:] != '.':
                record["record_data"] += '.'

            record_content = {
                "content": record["record_data"],
                "disabled":
                False if record['record_status'] == 'Active' else True
            }

            # Format the comment
            record_comments = [{
                "content": record["record_comment"],
                "account": ""
            }] if record.get("record_comment") else [{
                "content": "",
                "account": ""
            }]

            # Add the formatted record to rrsets list
            rrsets.append({
                "name": record_name,
                "type": record["record_type"],
                "ttl": int(record["record_ttl"]),
                "records": [record_content],
                "comments": record_comments
            })

        # Group the records which has the same name and type.
        # The rrset then has multiple records inside.
        transformed_rrsets = []

        # Sort the list before using groupby
        rrsets = sorted(rrsets, key=lambda r: (r['name'], r['type']))
        groups = groupby(rrsets, key=lambda r: (r['name'], r['type']))
        for _k, v in groups:
            group = list(v)
            transformed_rrsets.append(self.merge_rrsets(group))

        return transformed_rrsets

    def compare(self, domain_name, submitted_records):
        """
        Compare the submitted records with PDNS's actual data

        Args:
            domain_name(str): The zone name
            submitted_records(list): List of records submitted from PDA datatable

        Returns:
            new_rrsets(list): List of rrsets to be added
            del_rrsets(list): List of rrsets to be deleted
            zone_has_comments(bool): True if the zone currently contains persistent comments
        """
        # Create submitted rrsets from submitted records
        submitted_rrsets = self.build_rrsets(domain_name, submitted_records)
        current_app.logger.debug(
            "submitted_rrsets_data: \n{}".format(utils.pretty_json(submitted_rrsets)))

        # Current domain's rrsets in PDNS
        current_rrsets = self.get_rrsets(domain_name)
        current_app.logger.debug("current_rrsets_data: \n{}".format(
            utils.pretty_json(current_rrsets)))

        # Remove comment's 'modified_at' key
        # PDNS API always return the comments with modified_at
        # info, we have to remove it to be able to do the dict
        # comparison between current and submitted rrsets
        zone_has_comments = False
        for r in current_rrsets:
            for comment in r['comments']:
                if 'modified_at' in comment:
                    zone_has_comments = True
                    del comment['modified_at']

        # List of rrsets to be added
        new_rrsets = {"rrsets": []}
        for r in submitted_rrsets:
            if r not in current_rrsets and r['type'] in Setting(
            ).get_records_allow_to_edit():
                r['changetype'] = 'REPLACE'
                new_rrsets["rrsets"].append(r)

        # List of rrsets to be removed
        del_rrsets = {"rrsets": []}
        for r in current_rrsets:
            if r not in submitted_rrsets and r['type'] in Setting(
            ).get_records_allow_to_edit() and r['type'] != 'SOA':
                r['changetype'] = 'DELETE'
                del_rrsets["rrsets"].append(r)

        current_app.logger.debug("new_rrsets: \n{}".format(utils.pretty_json(new_rrsets)))
        current_app.logger.debug("del_rrsets: \n{}".format(utils.pretty_json(del_rrsets)))

        return new_rrsets, del_rrsets, zone_has_comments

    def apply_rrsets(self, domain_name, rrsets):
        headers = {'X-API-Key': self.PDNS_API_KEY, 'Content-Type': 'application/json'}
        jdata = utils.fetch_json(urljoin(
            self.PDNS_STATS_URL, self.API_EXTENDED_URL +
            '/servers/localhost/zones/{0}'.format(quote_plus(domain_name))),
                                  headers=headers,
                                  method='PATCH',
                                  verify=Setting().get('verify_ssl_connections'),
                                  data=rrsets)
        return jdata

    @staticmethod
    def to_api_payload(new_rrsets, del_rrsets, comments_supported):
        """Turn the given changes into a single api payload."""

        def replace_for_api(rrset):
            """Return a modified copy of the given RRset with changetype REPLACE."""
            if not rrset or rrset.get('changetype', None) != 'REPLACE':
                return rrset
            replace_copy = dict(rrset)
            has_nonempty_comments = any(bool(c.get('content', None)) for c in replace_copy.get('comments', []))
            if not has_nonempty_comments:
                if comments_supported:
                    replace_copy['comments'] = []
                else:
                    # For backends that don't support comments: Remove the attribute altogether
                    replace_copy.pop('comments', None)
            return replace_copy

        def rrset_in(needle, haystack):
            """Return whether the given RRset (identified by name and type) is in the list."""
            for hay in haystack:
                if needle['name'] == hay['name'] and needle['type'] == hay['type']:
                    return True
            return False

        def delete_for_api(rrset):
            """Return a minified copy of the given RRset with changetype DELETE."""
            if not rrset or rrset.get('changetype', None) != 'DELETE':
                return rrset
            delete_copy = dict(rrset)
            delete_copy.pop('ttl', None)
            delete_copy.pop('records', None)
            delete_copy.pop('comments', None)
            return delete_copy

        replaces = [replace_for_api(r) for r in new_rrsets]
        deletes = [delete_for_api(r) for r in del_rrsets if not rrset_in(r, replaces)]
        return {
            # order matters: first deletions, then additions+changes
            'rrsets': deletes + replaces
        }

    def apply(self, domain_name, submitted_records):
        """
        Apply record changes to a zone. This function
        will make 1 call to the PDNS API to DELETE and
        REPLACE records (rrsets)
        """
        current_app.logger.debug(
            "submitted_records: {}".format(submitted_records))

        # Get the list of rrsets to be added and deleted
        new_rrsets, del_rrsets, zone_has_comments = self.compare(domain_name, submitted_records)

        # The history logic still needs *all* the deletes with full data to display a useful diff.
        # So create a "minified" copy for the api call, and return the original data back up
        api_payload = self.to_api_payload(new_rrsets['rrsets'], del_rrsets['rrsets'], zone_has_comments)
        current_app.logger.debug(f"api payload: \n{utils.pretty_json(api_payload)}")

        # Submit the changes to PDNS API
        try:
            if api_payload["rrsets"]:
                result = self.apply_rrsets(domain_name, api_payload)
                if 'error' in result.keys():
                    current_app.logger.error(
                        'Cannot apply record changes. PDNS error: {}'
                        .format(result['error']))
                    return {
                        'status': 'error',
                        'msg': result['error'].replace("'", "")
                    }

            self.auto_ptr(domain_name, new_rrsets, del_rrsets)
            self.update_db_serial(domain_name)
            current_app.logger.info('Record was applied successfully.')
            return {'status': 'ok', 'msg': 'Record was applied successfully', 'data': (new_rrsets, del_rrsets)}
        except Exception as e:
            current_app.logger.error(
                "Cannot apply record changes to zone {0}. Error: {1}".format(
                    domain_name, e))
            current_app.logger.debug(traceback.format_exc())
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def auto_ptr(self, domain_name, new_rrsets, del_rrsets):
        """
        Add auto-ptr records
        """
        # Check if auto_ptr is enabled for this domain
        auto_ptr_enabled = False
        if Setting().get('auto_ptr'):
            auto_ptr_enabled = True
        else:
            domain_obj = Domain.query.filter(Domain.name == domain_name).first()
            domain_setting = DomainSetting.query.filter(
                DomainSetting.domain == domain_obj).filter(
                    DomainSetting.setting == 'auto_ptr').first()
            auto_ptr_enabled = strtobool(
                domain_setting.value) if domain_setting else False

        # If it is enabled, we create/delete the PTR records automatically
        if auto_ptr_enabled:
            try:
                RECORD_TYPE_TO_PTR = ['A', 'AAAA']
                new_rrsets = new_rrsets['rrsets']
                del_rrsets = del_rrsets['rrsets']

                if not new_rrsets and not del_rrsets:
                    msg = 'No changes detected. Skipping auto ptr...'
                    current_app.logger.info(msg)
                    return {'status': 'ok', 'msg': msg}

                new_rrsets = [
                    r for r in new_rrsets if r['type'] in RECORD_TYPE_TO_PTR
                ]
                del_rrsets = [
                    r for r in del_rrsets if r['type'] in RECORD_TYPE_TO_PTR
                ]

                d = Domain()
                for r in del_rrsets:
                    for record in r['records']:
                        # Format the reverse record name
                        # It is the reverse of forward record's content.
                        reverse_host_address = dns.reversename.from_address(
                            record['content']).to_text()

                        # Create the reverse domain name in PDNS
                        domain_reverse_name = d.get_reverse_domain_name(
                            reverse_host_address)
                        d.create_reverse_domain(domain_name,
                                                domain_reverse_name)

                        # Delete the reverse zone
                        self.name = reverse_host_address
                        self.type = 'PTR'
                        self.data = record['content']
                        self.delete(domain_reverse_name)

                for r in new_rrsets:
                    for record in r['records']:
                        # Format the reverse record name
                        # It is the reverse of forward record's content.
                        reverse_host_address = dns.reversename.from_address(
                            record['content']).to_text()

                        # Create the reverse domain name in PDNS
                        domain_reverse_name = d.get_reverse_domain_name(
                            reverse_host_address)
                        d.create_reverse_domain(domain_name,
                                                domain_reverse_name)

                        # Build the rrset for reverse zone updating
                        rrset_data = [{
                            "changetype":
                            "REPLACE",
                            "name":
                            reverse_host_address,
                            "ttl":
                            r['ttl'],
                            "type":
                            "PTR",
                            "records": [{
                                "content": r['name'],
                                "disabled": record['disabled']
                            }],
                            "comments": []
                        }]

                        # Format the rrset
                        rrset = {"rrsets": rrset_data}
                        self.add(domain_reverse_name, rrset)
                return {
                    'status': 'ok',
                    'msg': 'Auto-PTR record was updated successfully'
                }
            except Exception as e:
                current_app.logger.error(
                    "Cannot update auto-ptr record changes to zone {0}. Error: {1}"
                    .format(domain_name, e))
                current_app.logger.debug(traceback.format_exc())
                return {
                    'status':
                    'error',
                    'msg':
                    'Auto-PTR creation failed. There was something wrong, please contact administrator.'
                }

    def delete(self, domain):
        """
        Delete a record from zone
        """
        headers = {'X-API-Key': self.PDNS_API_KEY, 'Content-Type': 'application/json'}
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
                '/servers/localhost/zones/{0}'.format(quote_plus(domain))),
                                     headers=headers,
                                     timeout=int(
                                         Setting().get('pdns_api_timeout')),
                                     method='PATCH',
                                     verify=Setting().get('verify_ssl_connections'),
                                     data=data)
            current_app.logger.debug(jdata)
            return {'status': 'ok', 'msg': 'Record was removed successfully'}
        except Exception as e:
            current_app.logger.error(
                "Cannot remove record {0}/{1}/{2} from zone {3}. DETAIL: {4}"
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
        Check if record is present within zone records, and if it's present set self to found record
        """
        rrsets = self.get_rrsets(domain)
        for r in rrsets:
            if r['name'].rstrip('.') == self.name and r['type'] == self.type and r['records']:
                self.type = r['type']
                self.status = r['records'][0]['disabled']
                self.ttl = r['ttl']
                self.data = r['records'][0]['content']
                return True
        return False

    def update(self, domain, content):
        """
        Update single record
        """
        headers = {'X-API-Key': self.PDNS_API_KEY, 'Content-Type': 'application/json'}

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

        try:
            utils.fetch_json(urljoin(
                self.PDNS_STATS_URL, self.API_EXTENDED_URL +
                '/servers/localhost/zones/{0}'.format(quote_plus(domain))),
                             headers=headers,
                             timeout=int(Setting().get('pdns_api_timeout')),
                             method='PATCH',
                             verify=Setting().get('verify_ssl_connections'),
                             data=data)
            current_app.logger.debug("dyndns data: {0}".format(data))
            return {'status': 'ok', 'msg': 'Record was updated successfully'}
        except Exception as e:
            current_app.logger.error(
                "Cannot add record {0}/{1}/{2} to zone {3}. DETAIL: {4}".
                format(self.name, self.type, self.data, domain, e))
            return {
                'status': 'error',
                'msg':
                'There was something wrong, please contact administrator'
            }

    def update_db_serial(self, domain):
        headers = {'X-API-Key': self.PDNS_API_KEY}
        jdata = utils.fetch_json(urljoin(
            self.PDNS_STATS_URL, self.API_EXTENDED_URL +
            '/servers/localhost/zones/{0}'.format(quote_plus(domain))),
                                 headers=headers,
                                 timeout=int(
                                     Setting().get('pdns_api_timeout')),
                                 method='GET',
                                 verify=Setting().get('verify_ssl_connections'))
        serial = jdata['serial']

        domain = Domain.query.filter(Domain.name == domain).first()
        if domain:
            domain.serial = serial
            db.session.commit()
            return {
                'status': True,
                'msg': 'Synced local serial for zone name {0}'.format(domain)
            }
        else:
            return {
                'status': False,
                'msg':
                'Could not find zone name {0} in local db'.format(domain)
            }
