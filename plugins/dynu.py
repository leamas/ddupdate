'''
ddupdate plugin updating data on dynu.com.

See: ddupdate(8)

'''
import hashlib
from ddupdate.plugins_base import UpdatePlugin, get_response, get_netrc_auth


class DunyPlugin(UpdatePlugin):
    '''
    Update a dns entry on dynu.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin. As usual, any host updated must first be defined in the web UI

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

        user, password = get_netrc_auth('api.dynu.com')
        pw_hash = hashlib.md5(password.encode()).hexdigest()
        url = self._url.format(config.hostname, user, pw_hash)
        if ip:
            url += "&myip=" + ip
        get_response(log, url)
