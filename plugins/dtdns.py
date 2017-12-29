'''
ddupdate plugin updating data on dtdns.com. As usual, any
host updated ,ust first be defined in the web UI-

See: ddupdate(8)

'''
from ddupdate.plugins_base import UpdatePlugin, UpdateError
from ddupdate.plugins_base import get_response, get_netrc_auth


class DtdnsPlugin(UpdatePlugin):
    '''
    Update a dns entry on dtdns.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin. As usual any host updated must first be defined in the web UI

    .netrc: Use a line like:
        machine www.dtdns.com login <user>  password <password>

    Options:
        none
    '''
    _name = 'dtdns'
    _oneliner = 'Updates DNS data on dtdns.com'
    _url = "https://www.dtdns.com/api/autodns.cfm?id={0}&pw={1}"

    # pylint: disable=unused-variable

    def run(self, config, log, ip=None):

        user, password = get_netrc_auth('www.dtdns.com')
        url = self._url.format(config.hostname, password)
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
