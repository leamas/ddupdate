"""
ddupdate plugin updating data on cloudflare.com.

See: ddupdate(8)
See: https://api.cloudflare.com

"""
from requests import Request, Session
from requests.auth import AuthBase

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_netrc_auth, dict_of_opts


def _call(session, request):
    """Call Cloudflare V4 API."""
    try:
        prepped = session.prepare_request(request)
        res = session.send(prepped)

        if res.status_code / 100 != 2:
            raise ServiceError("Error retrieving %s: status %d" %
                               (request.url, res.status_code))
        json = res.json()
        if not json['success']:
            raise ServiceError("Error retrieving %s: errors %s" %
                               (request.url, json['errors']))
        return json['result']
    except ValueError as err:
        raise ServiceError("Error parsing response %s: %s" %
                           (request.url, err))


def _get_ipv4_from_dnsrecords(dnsrecords):
    """
    Find the A record in dns records, and return tuple (id, address).
    """
    for rec in dnsrecords:
        if 'type' in rec:
            if rec['type'] == 'A':
                return (rec['id'], rec['content'])
    return (None, None)


def _get_ipv6_from_dnsrecords(dnsrecords):
    """
    Find the AAAA record in dns records, and return tuple (id, address).
    """
    for rec in dnsrecords:
        if 'type' in rec:
            if rec['type'] == 'AAAA':
                return (rec['id'], rec['content'])
    return (None, None)


class CloudflareAuth(AuthBase):
    """
    Cloudflare Custom Authentication.

    Attaches a Cloudflare X-Auth-Email/Key authentication scheme to the given
    Request object.
    """

    def __init__(self, email, auth_key):
        """Email and auth_key are required."""
        self.email = email
        self.auth_key = auth_key

    def __call__(self, r):
        """Implement AuthBase."""
        r.headers['X-Auth-Email'] = self.email
        r.headers['X-Auth-Key'] = self.auth_key
        return r


class CloudflarePlugin(ServicePlugin):
    """
    Update a dns entry on cloudflare.com.

    Supports address plugins that define the IP, including default-web-ip
    and default-if. The ip-disabled plugin is not supported.
    ipv6 is supported

    Access to the service requires an API token and login email. This is
    available in the web interface. Also required is the name of the zone.

    netrc: Use a line like
        machine api.cloudflare.com login <email> password <authkey>
    Options:
        zone = Cloudflare Zone name (mandatory)
    """

    _name = 'cloudflare.com'
    _oneliner = 'Updates on https://cloudflare.com'
    _url = "https://api.cloudflare.com/client/v4"
    _auth = None

    def _get_zoneid(self, session, opts):
        """Retrieve an identifier for a given zone name."""
        zone = opts['zone']
        params = {
            'name': zone,
            'per_page': 1
        }
        request = Request(
            'GET',
            self._url + "/zones",
            params=params,
            auth=self._auth)
        res = _call(session, request)
        if res and len(res) == 1 and 'id' in res[0] and res[0]['id']:
            return res[0]['id']
        raise ServiceError("Zone %s not found" % zone)

    def _get_dnsrecords(self, session, hostname, opts):
        """Retrieve all dns records for a given hostname."""
        zone_id = opts['zone_id']
        params = {
            'name': hostname,
            'match': 'all',
        }
        request = Request(
            'GET',
            self._url + "/zones/{0}/dns_records".format(zone_id),
            params=params,
            auth=self._auth)
        return _call(session, request)

    def _create_dnsrecord(self, session, record, opts):
        """Create a new dns record."""
        zone_id = opts['zone_id']
        request = Request(
            'POST',
            self._url + "/zones/{0}/dns_records".format(zone_id),
            json=record,
            auth=self._auth)
        res = _call(session, request)
        return (res['id'], res['content'])

    def _update_dnsrecord(self, session, record_id, record, opts):
        """Update existing dns record."""
        zone_id = opts['zone_id']
        request = Request(
            'PUT',
            self._url + "/zones/{0}/dns_records/{1}".format(zone_id,
                                                            record_id),
            json=record,
            auth=self._auth)
        res = _call(session, request)
        return (res['id'], res['content'])

    def _init_auth(self):
        """Initialize Custom Authentication for Cloudflare v4 API."""
        user, password = get_netrc_auth('api.cloudflare.com')
        self._auth = CloudflareAuth(user, password)

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        if not ip:
            raise ServiceError("IP must be defined.")

        self._init_auth()
        opts = dict_of_opts(options)

        if 'zone' not in opts:
            raise ServiceError('Required option zone= missing, giving up.')

        session = Session()

        opts['zone_id'] = self._get_zoneid(session, opts)

        dnsrecords = self._get_dnsrecords(session, hostname, opts)
        ipv4_id, ipv4 = _get_ipv4_from_dnsrecords(dnsrecords)
        ipv6_id, ipv6 = _get_ipv6_from_dnsrecords(dnsrecords)
        log.debug("host=%s existing_ipv4=%s existing_ipv6=%s",
                  hostname, ipv4, ipv6)

        if ip.v4:
            if ipv4 != ip.v4:
                record = {
                    'type': 'A',
                    'name': hostname,
                    'content': ip.v4
                }
                if ipv4_id:
                    log.debug(
                        "method=update_A host=%s existing=%s expected=%s",
                        hostname, ipv4, ip.v4)
                    ipv4_id, ipv4 = self._update_dnsrecord(session,
                                                           ipv4_id,
                                                           record,
                                                           opts)
                else:
                    log.debug(
                        "method=create_A host=%s existing=%s expected=%s",
                        hostname, ipv4, ip.v4)
                    ipv4_id, ipv4 = self._create_dnsrecord(session,
                                                           record,
                                                           opts)
                log.debug("ipv4_id=%s updated_ipv4=%s", ipv4_id, ipv4)
            else:
                log.info("Existing ipv4 record matches, skipping update")

        if ip.v6:
            if ipv6 != ip.v6:
                record = {
                    'type': 'AAAA',
                    'name': hostname,
                    'content': ip.v6
                }
                if ipv6_id:
                    log.debug(
                        "method=update_AAAA host=%s existing=%s expected=%s",
                        hostname, ipv6, ip.v6)
                    ipv6_id, ipv6 = self._update_dnsrecord(session,
                                                           ipv6_id,
                                                           record,
                                                           opts)
                else:
                    log.debug(
                        "method=create_AAAA host=%s existing=%s expected=%s",
                        hostname, ipv6, ip.v6)
                    ipv6_id, ipv6 = self._create_dnsrecord(session,
                                                           record,
                                                           opts)
                log.debug("ipv6_id=%s updated_ipv6=%s", ipv6_id, ipv6)
            else:
                log.info("Existing ipv6 record matches, skipping update")
