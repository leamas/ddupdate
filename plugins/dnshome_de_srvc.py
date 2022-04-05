"""
ddupdate plugin updating data on dnshome.de.

See: ddupdate(8)
See: https://www.dnshome.de/
"""

from typing import AnyStr
from logging import Logger

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import http_basic_auth_setup, get_response, IpAddr


class DeDnsHomeAddressPlugin(ServicePlugin):
    """Update a dns entry on dnshome.de.

    Supports using most address plugins including default-web-ip, default-if
    and ip-disabled.

    You cannot set the host explicitly using a parameter like `hostname`.
    Even though the hostname is included in the query, it simply gets ignored.
    Set the host you want to update as username (like: subdomain.dnshome.de).

    Respects _global_ global `--ip-version` option.
    Be sure to configure ddupdate according to your connection type.

    netrc: Use a line like
        machine www.dnshome.de login <username>  password <password>

    Options:
        none
    """

    _name = 'dnshome.de'
    _oneliner = 'Updates on https://www.dnshome.de/'
    _url = "https://www.dnshome.de/dyndns.php?&hostname={0}"

    @staticmethod
    def is_success(response: AnyStr) -> bool:
        """Checks if the action was successful using the response.

        Args:
            response: The response-body to analyze.

        Returns:
            true, if the response-body starts with
                'good' - Update was successful
                'nochg' - No change was performed, since records were
                          already up to date.
        """
        return response.startswith('good') or response.startswith('nochg')

    def register(self, log: Logger, hostname: str, ip: IpAddr, options):
        """Implement ServicePlugin.register.

        Expects the `ip` to be filtered already according to the _global_
        `--ip-version` option.
        """
        url = self._url.format(hostname)

        if ip:
            if ip.v4:
                url += '&ip=' + ip.v4
            if ip.v6:
                url += '&ip6=' + ip.v6

        http_basic_auth_setup(url)

        body = get_response(log, url)  # Get ASCII encoded body-content
        if not DeDnsHomeAddressPlugin.is_success(body):
            raise ServiceError("Bad update reply.\nMessage: " + body)
