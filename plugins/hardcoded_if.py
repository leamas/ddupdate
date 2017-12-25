'''
ddupdate plugin providing an ip address to use.all

See: ddupdate(8)
'''

import subprocess
import sys

from plugins.plugins_base import IpPlugin, dict_of_opts


class HardcodedIfPlugin(IpPlugin):
    '''
    Use address on hardcoded interface

    Options: if=interface
    '''
    __version__ = '0.0.1'
    _name = 'hardcoded-if'
    _oneliner = 'Get address from a configuration option'

    def run(self, config, log, ip=None):
        opts = dict_of_opts(config.options)
        if 'if' not in opts:
            log.error("Required option if= missing, giving up.")
            sys.exit(2)
        iface = opts['if']
        use_next = False
        for word in subprocess.getoutput('ifconfig ' + iface).split():
            if use_next:
                return word
            use_next = word == 'inet'
        log.error("Cannot find address for %s, giving up", iface)
