'''
ddupdate plugin updating data on dynu.com. As usual, any
host updated ,ust first be defined in the web UI-

See: ddupdate(8)

'''
import hashlib
from netrc import netrc

from plugins.plugins_base import UpdatePlugin, UpdateError, get_response


class DunyPlugin(UpdatePlugin):
    '''
    Update a dns entry on dynu.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin.

    .netrc: Use a line like:
        machine api.dynu.com login <username> password <password>
    Options:
        none
    '''
    _name = 'dynu'
    _oneliner = 'Updates DNS data on dynu.com'
    _url = "http://api.dynu.com" \
        + "/nic/update?hostname={0}&username={1}&password={2}"

    def run(self, config, log, ip=None):

        auth = netrc().authenticators('api.dynu.com')
        if not auth:
            raise UpdateError("No password for api.duny.com found in .netrc")
        pw_hash = hashlib.md5(auth[2].encode()).hexdigest()
        url = self._url.format(config.hostname, auth[0], pw_hash)
        if ip:
            url += "&myip=" + ip
        get_response(log, url)
