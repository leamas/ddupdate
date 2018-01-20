"""
ddupdate dummy plugin making absolutely no update.

See: ddupdate(8)
"""

from ddupdate.ddplugin import ServicePlugin


class DryRunPlugin(ServicePlugin):
    """
    Prints the ip address obtained and configured hostname to update.

    Does not invoke any action. Primarely a debug tool.

    Options used: none
    """

    _name = 'dry-run'
    _oneliner = 'Debug dummy update plugin'
    _ip_cache_ttl = 1    # we do not cache these runs, right?

    def register(self, log, hostname, ip, options):
        """Run the actual module work."""
        print("dry-run: Using")
        print("    v4 address: %s\n    v6 address: %s\n    hostname: %s"
              % (ip.v4, ip.v6, hostname))
