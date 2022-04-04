"""
ddupdate plugin using nsupdate.

See: ddupdate(8)
See: nsupdate(1)
"""

from subprocess import Popen, PIPE
import sys

from ddupdate.ddplugin import ServicePlugin, ServiceError, dict_of_opts


class NsupdatePlugin(ServicePlugin):
    """
    Update a dns entry with nsupdate(1).

    Options (see manpage):
        server
        key
        zone
    """

    _name = 'nsupdate'
    _oneliner = 'Update address via nsupdate'

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register."""
        opts = dict_of_opts(options)
        log.debug(opts)
        if 'server' not in opts:
            log.error("Required server option missing, giving up")
            sys.exit(2)
        args = ('nsupdate',)
        if 'key' in opts:
            args += ('-k', opts['key'].encode('ascii'))
        with Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE) as p:
            p.stdin.write(b'server ' + opts['server'].encode('ascii') + b'\n')
            try:
                p.stdin.write(b'zone ' + opts['zone'].encode('ascii') + b'\n')
            except KeyError:
                pass
            hostname = hostname.encode('ascii')
            if ip:
                if ip.v4:
                    addr = ip.v4.encode('ascii')
                    p.stdin.write(b'update delete ' + hostname + b' A\n')
                    p.stdin.write(
                        b'update add ' + hostname + b' 60 A ' + addr + b'\n')
                if ip.v6:
                    addr = ip.v6.encode('ascii')
                    p.stdin.write(b'update delete ' + hostname + b' AAAA\n')
                    p.stdin.write(b'update add ' + hostname
                                  + b' 60 AAAA ' + addr + b'\n')
            p.stdin.write(b'send\n')
            err = p.communicate()[1]
        if len(err) > 0:
            raise ServiceError("Bad update reply: " + err.decode('ascii'))
