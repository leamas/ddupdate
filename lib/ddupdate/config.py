
"""Simple, CLI configuration script for ddupdate."""

import configparser
import logging
import os
import os.path
import re
import stat
import subprocess
import sys
import tempfile
import time

from straight.plugin import load

from ddupdate.main import setup, build_load_path
from ddupdate.ddplugin import ServicePlugin, AddressPlugin


_CONFIG_TRAILER = """
#
# Check for plugin options using ddupdate --help  <plugin name>
#
# service-options = foo bar
# address-options = foo bar
"""

_UPDATE_CONFIG = """
#!/bin/sh
if test -e {netrc_path}; then
    sed -E -i '/machine[ ]+{machine}/d' {netrc_path}
fi
if test "{netrc_line}" != "machine dummy"; then
    echo {netrc_line} >> {netrc_path}
fi
cp {config_src} {config_dest}
"""


class _GoodbyeError(Exception):
    """General error, implies sys.exit()."""

    def __init__(self, msg="", exitcode=0):
        Exception.__init__(self, msg)
        self.exitcode = exitcode
        self.msg = msg


def check_existing_files():
    """Check existing files and let user save them."""
    files = [
        '/etc/ddupdate.conf',
        os.path.expanduser('~/.netrc'),
        os.path.expanduser('~ddupdate/.netrc')
    ]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return
    print("The following configuration files already exists:")
    for f in files:
        print("        " + f)
    reply = input("OK to overwrite (Yes/No) [No]: ")
    if not reply or not reply.lower().startswith('y'):
        print("Please save and remove these file(s) and try again.")
        raise _GoodbyeError("", 0)


def _load_plugins(log, paths, plugin_class):
    """Load plugins into dict keyed by name."""
    plugins = {}
    for path in paths:
        sys.path.insert(0, path)
        these = load('plugins', plugin_class)
        these = these.produce()
        these_by_name = {plug.name(): plug for plug in these}
        for name, plugin in these_by_name.items():
            plugins.setdefault(name, plugin)
        sys.path.pop(0)
        log.debug("Loaded %d plugins from %s", len(plugins), path)
    return plugins


def _load_services(log, paths):
    """Load service plugins into dict keyed by name."""
    return _load_plugins(log, paths, ServicePlugin)


def _load_addressers(log, paths):
    """Load address plugins into dict keyed by name."""
    return _load_plugins(log, paths, AddressPlugin)


def get_service_plugin(service_plugins):
    """Present a menu with all plugins to user, let her select."""
    ix = 1
    services_by_ix = {}
    for id_ in sorted(service_plugins):
        print("%2d     %-18s     %s" %
              (ix, id_, service_plugins[id_].oneliner()))
        services_by_ix[ix] = service_plugins[id_]
        ix += 1
    text = input("Select service to use: ")
    try:
        ix = int(text)
    except ValueError:
        raise _GoodbyeError("Illegal number format", 1)
    if ix not in range(1, len(services_by_ix) + 1):
        raise _GoodbyeError("Illegal selection\n", 2)
    return services_by_ix[ix]


def get_address_plugin(log, paths, options):
    """Mumbo jumbo."""
    plugins = _load_addressers(log, paths)
    web_default_ip = plugins['default-web-ip']
    default_if = plugins['default-if']
    print("Probing for addresses, can take some time...")
    if_addr = default_if.get_ip(log, options)
    web_addr = web_default_ip.get_ip(log, options)
    print("1  Use address as seen from Internet [%s]" % web_addr.v4)
    print("2  Use address as seen on local network [%s]" % if_addr.v4)
    text = input("Select address to register (1, 2) [1]: ")
    text = text if text else '1'
    try:
        ix = int(text)
    except ValueError:
        raise _GoodbyeError("Illegal numeric input", 1)
    if ix == 1:
        return 'web-default-ip'
    elif ix == 2:
        return 'default-if'
    else:
        raise _GoodbyeError("Illegal value", 1)


def get_netrc(service):
    """
    Using docstring in service.

    Return netrc line with user supplied user, pasword etc.
    original line.
    """
    lines = service.info().split('\n')
    line = ''
    for line in lines:
        if line.strip().startswith('machine'):
            break
    else:
        return None
    matches = re.findall('<([^>]+)>', line)
    for item in matches:
        value = input("[%s] %s :" % (service.name(), item))
        line = line.replace('<' + item + '>', value)
    return line


def merge_configs(line, netrc_path, config_src, config_dest, cmd):
    """Merge line into existing .netrc file and cp src to dest using cmd."""
    line = line if line else "machine dummy"
    script = _UPDATE_CONFIG.format(
        netrc_line=line,
        machine=line.split()[1],
        netrc_path=netrc_path,
        config_src=config_src,
        config_dest=config_dest
    )
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(script.encode())
    os.chmod(f.name, stat.S_IRUSR | stat.S_IXUSR)
    subprocess.run(cmd(f.name))
    os.unlink(f.name)
    print("Patched .netrc: " + netrc_path)
    print("Patched config: " + config_dest)


def update_config(config, path):
    """Merge values from config dict into file on path, return tmpfile."""
    parser = configparser.SafeConfigParser()
    try:
        parser.read(path)
    except configparser.Error:
        pass
    else:
        if "update" in parser:
            for key in config:
                if key in parser['update']:
                    config[key] = parser['update'][key]
    header = '# Created by ddupdate-config at %s\n' % time.asctime()
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write(header)
        parser.write(f)
        if ('service-options' or 'address-options') not in parser:
            f.write(_CONFIG_TRAILER)
        f.flush()
    return f.name


def write_config_files(config, netrc_line):
    """Merge user config data into user config-files."""
    confdir =  os.path.expanduser("~/.config")
    if not os.path.exists(confdir):
        os.makedirs(confdir)
    tmp_conf = update_config(config, os.path.join(confdir, "ddupdate.conf"))
    merge_configs(netrc_line,
                  os.path.expanduser('~/.netrc'),
                  tmp_conf,
                  os.path.expanduser("~/.config/ddupdate.conf"),
                  lambda p: ["/bin/sh", p])
    os.unlink(tmp_conf)


def write_root_files(config, netrc_line):
    """Merge user config data into system-wide config-files root."""
    tmp_conf = update_config(config, "/etc/ddupdate.conf")
    merge_configs(netrc_line,
                  os.path.expanduser('~ddupdate/.netrc'),
                  tmp_conf,
                  '/etc/ddupdate.conf',
                  lambda p: ["/usr/bin/sudo", p])
    os.unlink(tmp_conf)


def main():
    """Indeed: main function."""
    try:
        check_existing_files()
        log, opts = setup()
        log.setLevel(logging.WARNING)
        load_paths = build_load_path(log)
        service_plugins = _load_services(log, load_paths)
        service = get_service_plugin(service_plugins)
        netrc = get_netrc(service)
        hostname = input("[%s] Hostname: " % service.name())
        address_plugin = get_address_plugin(log, load_paths, opts)
        print("Address plugin :" + address_plugin)
        conf = {
            'address-plugin': address_plugin,
            'service-plugin': service.name(),
            'hostname': hostname
        }
        write_config_files(conf, netrc)
        print("Patching as root: /etc/ddupdate.conf and ~ddupdate/.netrc")
        write_root_files(conf, netrc)
    except _GoodbyeError as err:
        if err.exitcode != 0:
            sys.stderr.write("Fatal error: " + str(err) + "\n")
        sys.exit(err.exitcode)


if __name__ == '__main__':
    main()


# vim: set expandtab ts=4 sw=4:
