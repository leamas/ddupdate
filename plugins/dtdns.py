'''
ddupdate plugin updating data on dtdns.com. As usual, any
host updated ,ust first be defined in the web UI-

See: ddupdate(8)

'''
from netrc import netrc

from plugins.plugins_base import UpdatePlugin, UpdateError, get_response


class DtdnsPlugin(UpdatePlugin):
    '''
    Update a dns entry on dtdns.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin.

    .netrc: Use a line like:
        machine www.dtdns.com login <user>  password <password>
    Options:
        none
    '''
    _name = 'dtdns'
    _oneliner = 'Updates DNS data on dtdns.com'
    _url = "https://www.dtdns.com/api/autodns.cfm?id={0}&pw={1}"

    def run(self, config, log, ip=None):

        auth = netrc().authenticators('www.dtdns.com')
        if not auth:
            raise UpdateError("No password for dtns.com found in .netrc")
        url = self._url.format(config.hostname, auth[2])
        if ip:
            url += "&ip=" + ip
        try:
            html = get_response(log, url)
        except TimeoutError:
            # one more try...
            html = get_response(log, url)
        if 'points to' not in html:
            raise UpdateError("Bad update reply: " + html)
        log.info("Update completed: " + html)
