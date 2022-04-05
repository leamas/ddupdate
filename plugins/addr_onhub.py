"""
ddupdate plugin to retrieve address from an OnHub / Google / Nest router.

See: ddupdate(8)
"""

import json
import urllib.request

from ddupdate.ddplugin import AddressPlugin, AddressError, IpAddr


# onhub.here should resolve correctly if you have this type of router
_URL = "http://onhub.here/api/v1/status"


class OnHubPlugin(AddressPlugin):
    """
    Get the external address via the OnHub status API.

    Options used: none
    """

    _name = "onhub"
    _oneliner = "Obtain external address from OnHub / Google / Nest router"

    def get_ip(self, log, options):
        """Implement AddressPlugin.get_ip()."""
        # Documentation refers to testing on 3.4
        # f-strings are from 3.6 and exception chaining from 3.9
        # pylint: disable=raise-missing-from
        log.debug("trying " + _URL)
        try:
            with urllib.request.urlopen(_URL) as response:
                if response.getcode() != 200:
                    raise AddressError(
                        "Bad response %s from %s" % (response.getcode(), _URL)
                    )
                status = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as err:
            raise AddressError("Error reading %s :%s" % (_URL, err))
        log.debug("Got response: %s", json.dumps(status))

        log.debug("WAN online: %s", status["wan"]["online"])

        return IpAddr(status["wan"]["localIpAddress"])
