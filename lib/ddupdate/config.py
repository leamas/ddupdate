
"""Simple, CLI configuration script for ddupdate."""

import configparser
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from ddupdate.main import \
    log_setup, build_load_path, envvar_default, load_plugin_dir
from ddupdate.ddplugin import ServicePlugin, AddressPlugin, AuthPlugin


_CONFIG_TRAILER = """
#
# Check for plugin options using ddupdate --help  <plugin name>
#
# service-options = foo bar
# address-options = foo bar
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
    files = [os.path.join(confdir, 'ddupdate.conf')]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return
    print("The following configuration file(s) already exists:")
    for f in files:
        print("        " + f)
    reply = input("OK to overwrite (Yes/No) [No]: ")
    if not reply or not reply.lower().startswith('y'):
        print("Please save these file(s) and try again.")
        raise _GoodbyeError("", 0) from None


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


def _load_auth_plugins(log, paths):
    """Load auth plugins from paths into dict keyed by name."""
    return _load_plugins(log, paths, AuthPlugin)


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
        raise _GoodbyeError("Illegal number format", 1) from None
    if ix not in range(1, len(services_by_ix) + 1):
        raise _GoodbyeError("Illegal selection\n", 2) from None
    return services_by_ix[ix]


def get_auth_plugin(plugins):
    """
    Present a menu with all auth plugins to user, let her select.

    Parameters:
      - plugins: Dict of loaded plugins keyed by plugin.name()

    Return:
      A loaded plugin as selected by user.

    """
    print("\nAvailable backends for storing passwords")
    ix = 1
    plugins_by_ix = {}
    for id_ in sorted(plugins):
        print("%2d     %-18s     %s" %
              (ix, id_, plugins[id_].oneliner()))
        plugins_by_ix[ix] = plugins[id_]
        ix += 1
    text = input("Select backend (use keyring if in doubt): ")
    try:
        ix = int(text)
    except ValueError:
        raise _GoodbyeError("Illegal number format", 1) from None
    if ix not in range(1, len(plugins_by_ix) + 1):
        raise _GoodbyeError("Illegal selection\n", 2) from None
    return plugins_by_ix[ix]


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
    if_addr = default_if.get_ip(log, [])
    web_addr = web_default_ip.get_ip(log, [])
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
    raise _GoodbyeError("Illegal value", 1) from None


def copy_systemd_units():
    """Copy system-wide templates to ~/.config/systemd/user."""
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    user_dir = os.path.join(confdir, 'systemd/user')
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    here = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    srcdir = os.path.join(here, '..', '..', 'systemd')
    if not os.path.exists(srcdir):
        srcdir = "/usr/local/share/ddupdate/systemd"
        if not os.path.exists(srcdir):
            srcdir = "/usr/share/ddupdate/systemd"

    path = os.path.join(user_dir, "ddupdate.service")
    if not os.path.exists(path):
        shutil.copy(os.path.join(srcdir, "ddupdate.service"), path)
    path = os.path.join(user_dir, "ddupdate.timer")
    if not os.path.exists(path):
        shutil.copy(os.path.join(srcdir, "ddupdate.timer"), path)

    # Ad-hoc logic: Use script in /usr/local/bin or /usr/bin if existing,
    # else the one in current dir. This is practical although not quite
    # consistent.
    installconf_path = os.path.join(here, "install.conf")
    parser = configparser.SafeConfigParser()
    try:
        parser.read(installconf_path)
    except configparser.Error:
        parser.clear()
    if 'install' in parser:
        bindir = parser['install']['install_scripts']
    else:
        bindir = os.path.abspath(os.path.join(here, '..', '..'))
    with open(os.path.join(user_dir, 'ddupdate.service')) as f:
        lines = f.readlines()
    output = []
    for line in lines:
        if line.startswith('ExecStart'):
            output.append("ExecStart=" + bindir + "/ddupdate")
        else:
            output.append(line)
    with open(os.path.join(user_dir, 'ddupdate.service'), 'w') as f:
        f.write('\n'.join([elem.strip() for elem in output]))


def get_netrc(service):
    """Get .netrc line for service.

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


def write_config_files(config):
    """
    Merge user config data into user config file.

    Parameters:
      - config: dict with new configuration options.

    Updates:
      ~/.config/ddupdate.conf, respecting XDG_CONFIG_HOME.

    """
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    if not os.path.exists(confdir):
        os.makedirs(confdir)
    dest = os.path.join(confdir, "ddupdate.conf")
    tmp_conf = update_config(config, dest)
    shutil.copyfile(tmp_conf, os.path.join(confdir, "ddupdate.conf"))
    os.unlink(tmp_conf)
    print("Patched config file: " + dest)


def write_credentials(auth_plugin, hostname, netrc):
    """Update credentials at auth_plugin with data from netrc."""
    username = None
    password = None
    if not netrc:
        print("NOTE: No credentials defined")
        return
    words = netrc.split(' ')
    words = [word for word in words if word]
    for i in range(0, len(words) - 1):
        if words[i] == 'machine':
            hostname = words[i + 1].lower()
        if words[i] == 'login':
            username = words[i + 1]
        if words[i] == 'password':
            password = words[i + 1]
    auth_plugin.set_password(hostname, username, password)
    print("Updated password for user %s at %s" % (username, hostname))


def try_start_service():
    """Start dduppdate systemd user service and display logs."""
    print("Starting service and displaying logs")
    cmd = 'systemctl --user daemon-reload'
    cmd += ';systemctl --user start ddupdate.service'
    cmd += ';journalctl -l --user --since -60s -u ddupdate.service'
    cmd = ['sh', '-c', cmd]
    subprocess.run(cmd, check=True)
    print('Use "journalctl --user -u ddupdate.service" to display logs.')


def enable_service():
    """Enable/start service and timer as user determines."""
    reply = input("Shall I run service regularly (Yes/No) [No]: ")
    do_start = reply and reply.lower().startswith('y')
    if do_start:
        cmd = 'systemctl --user start ddupdate.timer'
        cmd += ';systemctl --user enable ddupdate.timer'
        print("\nStarting and enabling ddupdate.timer")
        try:
            subprocess.run(['sh', '-c', cmd], check=True)
        except subprocess.CalledProcessError as err:
            raise _GoodbyeError(
                "Cannot start ddupdate.timer: " + str(err), 2) from None
    else:
        cmd = 'systemctl --user stop ddupdate.timer'
        cmd += 'systemctl --user disable ddupdate.timer'
        print("Stopping ddupdate.timer")
        try:
            subprocess.run(['sh', '-c', cmd], check=True)
        except subprocess.CalledProcessError as err:
            print("Cannot stop ddupdate.timer (already stopped?)")
        msg = "systemctl --user start ddupdate.timer"
        msg += "; systemctl --user enable ddupdate.timer"
        print('\nStart ddupdate using "%s"' % msg)
    print("To run service from boot and after logout do "
          + '"sudo loginctl enable-linger $USER"')


def main():
    """Indeed: main function."""
    try:
        log = log_setup()
        check_existing_files()
        copy_systemd_units()
        load_paths = build_load_path(log)
        service_plugins = _load_services(log, load_paths)
        service = get_service_plugin(service_plugins)
        netrc = get_netrc(service)
        auth_plugins = _load_auth_plugins(log, load_paths)
        auth_plugin = get_auth_plugin(auth_plugins)
        hostname = input("[%s] hostname: " % service.name())
        address_plugin = get_address_plugin(log, load_paths)
        conf = {
            'address-plugin': address_plugin,
            'service-plugin': service.name(),
            'hostname': hostname,
            'auth-plugin': auth_plugin.name()
        }
        write_credentials(auth_plugin, hostname, netrc)
        write_config_files(conf)
        try_start_service()
        enable_service()
    except _GoodbyeError as err:
        if err.exitcode != 0:
            sys.stderr.write("Fatal error: " + str(err) + "\n")
        sys.exit(err.exitcode)


if __name__ == '__main__':
    main()


# vim: set expandtab ts=4 sw=4:
