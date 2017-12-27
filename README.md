# ddupdate - update dns data for dynamic ip addresses.

## General

ddupdate is a tool for automatically updating dns data for a system using
e. g., DHCP. The goal is it should be possible to access a system with a
fixed dns name such as myhost.somewhere.net even if the IP  address is
changed.

From another perspective, ddupdate is a tool replicating part of the
existing ddclient functionality, but with a better overall design and user
interaction. In particular, it has better help, logging and documentation.
Thanks to the plugin design, it's also much easier to provide support for
new services and address detection strategies.

## Status

Like... well, alpha. Fresh code, here is probably bugs lurking around.
That said, here is support for duckdns, afraid.org, no-ip.com and dynu.com.
IP addresses to register can be retrieved in a multitude of ways from
none at all (trusting the service provider) to the generic 'cmd' plugin
which can use the output from a command.

Writing new plugins for not-so-odd services should not be fairly simple
given the examples available.

## Dependencies

Just a few:
   - python3
   - python3-straight-plugin
   - python3-setuptools
   - The /usr/bin/ip command is used in some plugins.

## Installation

ddupdate can be run as a regular user straight off the cloned git directory.
To make a test version possible to run from anywhere make a symlink:

    $ ln -s $PWD/src/ddupdate§i/ddupdate $HOME/bin/ddupdate

It's also possible to make a user installation, using a horrible cludge:

    $ USER_INSTALL_FIX=1 python3 setup.py install --user

To make a local installation in /usr/local run something like

    $ sudo python3 setup.py --prefix=/usr/local

## Configuration

Configuration is basically about selecting a plugin for a specific ddns
service and possibly another plugin which provides the ip address to be
registered. Some plugins needs specific options.

First question is what kind of ip address which should be registered. The
most common case is to use the address as seen from the internet.
This makes it possible for users on internet to access the machine.

On the other hand, it might be necessary to register another type of
address for example when using DHCP addresses on an internal network behind
a router and the machine should be reached by users on this network.
In this case the machine's real address should be registered.

First, list all plugins:

    $ ddupdate --list-plugins ip-plugins
    ip-disabled          Force update service to provide ip address
    ip-from-command      Obtain address from a command
    default-if           Get ip address from default interface (linux)
    default-web-ip       Obtain external address as seen from the net
    hardcoded-if         Get address from a configuration option
    $ ddupdate --list-plugins services
    no-ip                Updates DNS data on no-ip.com
    duckdns              Update DNS data on duckdns.org
    dynu                 Updates DNS data on dynu.com
    changeip             Updates DNS data on changip.com
    freedns              Updates host on freedns.afraid.org
    dtdns                Updates DNS data on dtdns.com
    dnsexit              Updates host on www.dnsexit.com
    dry-run              Debug dummy update plugin


Next, pick an update plugin and check the help info, here dynu:

    $ ddupdate --help dynu
    Name: dynu
    Source: /home/al/src/ddupdate/src/ddupdate/plugins/plugins_base.py

    Update a dns entry on dynu.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin.

    netrc: Uses username/password for machine api.dynu.com.
    Options used: none

If all looks good, register on dynu.com. This will end up in a hostname,
username and password. Create an entry in the ~/.netrc file like:

    machine api.dynu.com login <username> password <secret>

Note that this file must be protected for other users (otherwise no tools
will accept it). Do:

    $ chmod 600 ~/.netrc

Now, let's select the plugin which provides the ip address to register.
For the default case, the default-web-ip plugin generates the address as
seen from the network. This can be tested using:

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dry-run
    dry-run: Using address 90.224.208.212 and hostname host.nowhere.net

All looks good. Now, let's try to actually update that hostname on dynu.com:

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dynu \
      --hostname myhost.dynu.net -L info
    INFO - Loglevel: INFO
    INFO - Using hostname: myhost.dynu.net
    INFO - Using ip address plugin: default-web-ip
    INFO - Using service plugin: dynu
    INFO - Plugin options:
    INFO - Using ip address: 90.224.208.212
    INFO - Update OK

Again fine. Update /etc/ddupdate.conf to something like

    [update]
    address-plugin = web-default-ip
    service-plugin = dynu
    hostname = myhost.dynu.net
    loglevel = info

After which it should be possible to just invoke *ddupdate* without
any options.

## Configuring systemd

systemd is used to invoke ddupdate periodically. The safest bet is
not to use the upstream systemd files. Do:

    $ sudo cp /lib/systemd/system/ddupdate* /etc/systemd/system

Check the two /etc/ files, in particular for paths. Test the service and
the logged info:

    $ sudo systemctl daemon-reload
    $ sudo systemcl start ddupdate.service
    $ sudo journalctl -u ddupdate.service

When all is fine make sure ddupdate is run hourly using:

    $ sudo systemctl start ddupdate.timer
    $ sudo systemctl enable ddupdate.timer

## Configuring NetworkManager

NetworkManager can be configured to start/stop ddupdate when interfaces goes
up or down. An example script to drop in /etc/NetworkManager/dispatcher.d
is distributed in the package.

## Packaging

  - fedora is packaged in the *fedora* branch. Building requires the fedora
    toolchain in the *rpmdevtools* and *rpm-build* packages. To build:

        $ git clone -b fedora git clone https://github.com/leamas/ddupdate.git
        $ cd ddupdate
        $ spectool -g ddupdate.spec
        $ rpmbuild -D "_sourcedir $PWD" -ba ddupdate.spec

    This creates both a source and a binary package underneath *rpmbuild*.

  - The debian packaging is based on gbp and lives in the *debian* and
    *pristine-tar* branches.  The packages *git-buildpackage*, *devscripts*
    and *git*  are required to build. To build current version 0.1 do:

        $ git clone -b debian https://github.com/leamas/ddupdate.git
        $ cd ddupdate
        $ gbp buildpackage --git-upstream-tag=0.1
        $ git clean -fd    # To be able to rebuild
