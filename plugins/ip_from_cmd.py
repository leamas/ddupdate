"""
ddupdate plugin supporting getting ip address from a command.

See: ddupdate(8)

"""

import re
import subprocess

from ddupdate.ddplugin import \
    AddressPlugin, AddressError, IpAddr, dict_of_opts


class IpFromCmdPlugin(AddressPlugin):
    """
    Use ip4 address obtained from a command.

    The command is invoked without parameters, and should return one or
    two space-separated words on stdout. Each word must either a valid
    ipv4 or ipv6 address. Anything which is not parsed as addresses
    is treated as an error message.

    Note that when invoked in a systemd context, the environment
    for the command is more or less empty.

    The command invoked is specified in the cmd option

    Options:
        cmd=command

    netrc:
        Nothing
    """

    _name = 'ip-from-command'
    _oneliner = 'Obtain address from a command'

    def get_ip(self, log, options):
        """Implement AddressPlugin.get_ip()."""
        opts = dict_of_opts(options)
        if 'cmd' not in opts:
            raise AddressError('Required option cmd= missing, giving up.')
        cmd = opts['cmd']
        log.debug('Running: %s', cmd)
        addr = IpAddr()
        result = subprocess.getoutput(cmd).strip()
        log.debug('result: %s', result)
        pat = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        pat6 = re.compile(r'[:0-9a-f]{12,}(\s|\Z)')
        for word in result.split():
            if pat.fullmatch(word):
                addr.v4 = word
            elif pat6.fullmatch(word):
                addr.v6 = word
            else:
                raise AddressError(
                    'Cannot parse command output: ' + result)
        return addr
