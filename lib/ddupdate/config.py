
"""Simple, CLI configuration script for ddupdate."""

import configparser
import logging
import os
import os.path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

from ddupdate.main import \
    setup, build_load_path, envvar_default, load_plugin_dir
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
chmod 600 {netrc_path}
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
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    files = [
        os.path.expanduser('~/.netrc'),
        os.path.join(confdir, 'ddupdate.conf')
    ]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return
    print("The following configuration file(s)s already exists:")
    for f in files:
        print("        " + f)
    reply = input("OK to overwrite (Yes/No) [No]: ")
    if not reply or not reply.lower().startswith('y'):
        print("Please save these file(s) and try again.")
        raise _GoodbyeError("", 0)


def _load_plugins(log, paths, plugin_class):
    """
    Load plugins into dict keyed by name.

    Parameters:
      - log: Standard python log instance.
      - paths: List of strings, path candidates containing plugins.
      - plugin_class: Type, base class of plugins to load.

    Returns:
      dict of loaded plugins with plugin.name() as key.

    """
    plugins = {}
    for path in paths:
        these = load_plugin_dir(os.path.join(path, 'plugins'), plugin_class)
        these_by_name = {plug.name(): plug for plug in these}
        for name, plugin in these_by_name.items():
            plugins.setdefault(name, plugin)
        log.debug("Loaded %d plugins from %s", len(plugins), path)
    return plugins


def _load_services(log, paths):
    """Load service plugins from paths into dict keyed by name."""
    return _load_plugins(log, paths, ServicePlugin)


def _load_addressers(log, paths):
    """Load address plugins from paths into dict keyed by name."""
    return _load_plugins(log, paths, AddressPlugin)


def get_service_plugin(service_plugins):
    """
    Present a menu with all plugins to user, let her select.

    Parameters:
      - service_plugins: Dict of loaded plugins keyed by plugin.name()

    Return:
      A loaded plugin as selected by user.

    """
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


def get_address_plugin(log, paths):
    """
    Let user select address plugin.

    Parameters:
      - log: Standard python log instance.
      - paths: List of strings, directory paths to load plugins from.

    Return:
      Name of selected address plugin.

    """
    plugins = _load_addressers(log, paths)
    web_default_ip = plugins['default-web-ip']
    default_if = plugins['default-if']
    print("Probing for addresses, can take some time...")
    if_addr = default_if.get_ip(log, {})
    web_addr = web_default_ip.get_ip(log, {})
    print("1  Use address as seen from Internet [%s]" % web_addr.v4)
    print("2  Use address as seen on local network [%s]" % if_addr.v4)
    print("3  Use address as decided by service")
    ix = input("Select address to register (1, 2, 3) [1]: ").strip()
    ix = ix if ix else '1'
    plugin_by_ix = {
        '1': 'default-web-ip', '2': 'default-if', '3': 'ip-disabled'
    }
    if ix in plugin_by_ix:
        return plugin_by_ix[ix]
    else:
        raise _GoodbyeError("Illegal value", 1)


def copy_systemd_units():
    """Copy system-wide templates to ~/.config/systemd/user."""
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    user_dir = os.path.join(confdir, 'systemd/user')
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    path = os.path.join(user_dir, "ddupdate.service")
    if not os.path.exists(path):
        shutil.copy("/usr/share/ddupdate/systemd/ddupdate.service", path)
    path = os.path.join(user_dir, "ddupdate.timer")
    if not os.path.exists(path):
        shutil.copy("/usr/share/ddupdate/systemd/ddupdate.timer", path)


def get_netrc(service):
    """
    Get .netrc line for service.

    Looks into the service class documentation for a line starting
    with 'machine' and returns it after substituting values in
    angle brackets lke <username> with values supllied by user.

    Parameters:
      - service: Loaded service plugin.

    Return:
      netrc line with <user>, <password>, etc., as substituted by user.

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


def merge_configs(netrc_line, netrc_path, config_src, config_dest, cmd):
    """
    Merge netrc and config file options into current configuration.

    Parameters:
      - netrc_line: String, new netrc authentication line.
      - netrc_path: String, path of netrc file.
      - config_src: String, path of updated, temporary config file.
      - config_dest: String, path of existing config file actually used.
      - cmd: function(path) returning command executing path in a shell,
             a list of strings.

    Returns nothing.

    """
    netrc_line = netrc_line if netrc_line else "machine dummy"
    script = _UPDATE_CONFIG.format(
        netrc_line=netrc_line,
        machine=netrc_line.split()[1],
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
    """
    Merge values from config dict and existing conf into tempfile.

    Parameters:
      - config: dict of new configuration options.
      - path:  Path to existing config file.

    Return:
      Path to temporary config file with updated options.

    """
    parser = configparser.SafeConfigParser()
    try:
        parser.read(path)
    except configparser.Error:
        parser.clear()
    parser.setdefault('update', {})
    parser['update'].setdefault('ip-version', 'v4')
    parser['update'].setdefault('loglevel', 'info')
    parser['update'].update(config)
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write('# Created by ddupdate-config at %s\n' % time.asctime())
        parser.write(f)
        if ('service-options' or 'address-options') not in parser:
            f.write(_CONFIG_TRAILER)
        f.flush()
    return f.name


def write_config_files(config, netrc_line):
    """
    Merge user config data into user config files.

    Parameters:
      - config: dict with new configuration options.
      - netrc_line: Authentication line to merge into existing .netrc file.

    Updates:
      ~/.config/ddupdate.conf and ~/.netrc, respecting XDG_CONFIG_HOME.

    """
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    if not os.path.exists(confdir):
        os.makedirs(confdir)
    tmp_conf = update_config(config, os.path.join(confdir, "ddupdate.conf"))
    merge_configs(netrc_line,
                  os.path.expanduser('~/.netrc'),
                  tmp_conf,
                  os.path.join(confdir, "ddupdate.conf"),
                  lambda p: ["/bin/sh", p])
    os.unlink(tmp_conf)


def try_start_service():
    """Start dduppdate systemd user service and display logs."""
    print("Starting service and displaying logs")
    cmd = 'systemctl --user daemon-reload'
    cmd += ';systemctl --user start ddupdate.service'
    cmd += ';journalctl -l --user --since -60s -u ddupdate.service'
    cmd = ['sh', '-c', cmd]
    subprocess.run(cmd)
    print('Use "journalctl --user -u ddupdate.service" to display logs.')


def enable_service():
    """Enable/start service and timer as user determines."""
    reply = input("Shall I run service regularly (Yes/No) [No]: ")
    do_start = reply and reply.lower().startswith('y')
    if do_start:
        cmd = 'systemctl --user start ddupdate.timer'
        cmd += ';systemctl --user enable ddupdate.timer'
        print("\nStarting and enabling ddupdate.timer")
        subprocess.run(['sh', '-c', cmd])
    else:
        cmd = 'systemctl --user stop ddupdate.timer'
        cmd += 'systemctl --user disable ddupdate.timer'
        print("Stopping ddupdate.timer")
        subprocess.run(['sh', '-c', cmd])
        msg = "systemctl --user start ddupdate.timer"
        msg += "; systemctl --user enable ddupdate.timer"
        print('\nStart ddupdate using "%s"' % msg)
    print("To run service from boot and after logout do "
          + '"sudo loginctl enable-linger $USER"')


def main():
    """Indeed: main function."""
    try:
        log = setup(logging.WARNING)[0]
        check_existing_files()
        copy_systemd_units()
        load_paths = build_load_path(log)
        service_plugins = _load_services(log, load_paths)
        service = get_service_plugin(service_plugins)
        netrc = get_netrc(service)
        hostname = input("[%s] hostname: " % service.name())
        address_plugin = get_address_plugin(log, load_paths)
        conf = {
            'address-plugin': address_plugin,
            'service-plugin': service.name(),
            'hostname': hostname
        }
        write_config_files(conf, netrc)
        try_start_service()
        enable_service()
    except _GoodbyeError as err:
        if err.exitcode != 0:
            sys.stderr.write("Fatal error: " + str(err) + "\n")
        sys.exit(err.exitcode)


if __name__ == '__main__':
    main()


# vim: set expandtab ts=4 sw=4:
