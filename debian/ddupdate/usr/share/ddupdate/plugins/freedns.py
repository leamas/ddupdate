'''
ddupdate plugin updating data on freedns.org.

See: ddupdate(8)
'''
import hashlib
from netrc import netrc

from plugins.plugins_base import UpdatePlugin, UpdateError, get_response


class FreednsPlugin(UpdatePlugin):
    '''
    Updates DNS data for host on freedns.afraid.org.

    Freedns will always use the external address as seen from afraid.org,
    so the ip address we provide using the ip plugin is actually not
    used. This means that afraid.org does not support internal addresses
    not visible from the net. For these reasons the ip-disabled plugin is
    the recommended one for freedns.

    netrc: Use a line like
        machine freedns.afraid.org login <username> password <password>
    Options:
        None
    '''
    _name = 'freedns'
    _oneliner = 'Updates host on freedns.afraid.org'
    _url = 'http://freedns.afraid.org/api/?action=getdyndns&sha={0}'

    def run(self, config, log, ip=None):
        '''
        Based on http://freedns.afraid.org/api/, needs _url below  to update.
        The sha parameter is sha1sum of login|password.  This returns a list
        of host|currentIP|updateURL lines.  Pick the line that matches myhost,
        and fetch the URL.  word 'Updated' for success, 'fail' for failure.
        '''
        def build_shasum():
            ''' Compute sha1sum('user|password') used in url. '''
            auth = netrc().authenticators('freedns.afraid.org')
            if auth is None:
                raise UpdateError(
                    "No username/password for freedns.afraid.org in .netrc")
            token = "{0}|{1}".format(auth[0], auth[2])
            return hashlib.sha1(token.encode()).hexdigest()

        if ip:
            log.warn("Ignoring supplied address, using freedns computed one")
            log.info("Consider using the ip-disabled plugin with freedns")
        shasum = build_shasum()
        url = self._url.format(shasum)
        html = get_response(log, url)
        update_url = None
        for line in html.split("\n"):
            log.debug("Got line: " + line)
            tokens = line.split("|")
            if tokens[0] == config.hostname:
                update_url = tokens[2]
                break
        if not update_url:
            raise UpdateError(
                "Cannot see %s being set up at this account" % config.hostname)
        log.debug("Contacting freedns for update on %s", update_url)
        get_response(log, update_url)
