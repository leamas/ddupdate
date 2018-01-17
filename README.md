ddupdate - update dns data for dynamic ip addresses.
====================================================

General
-------

ddupdate is a tool for automatically updating dns data for a system using
for example DHCP. It makes it  possible to access the system with
a fixed dns name such as myhost.somewhere.net even if the IP address is
changed. It is a linux-centric, user-friendly, flexible and maintainable
alternative to the ubiquitous ddclient.


Status
------

Like... well, alpha. Fresh code, here is probably bugs lurking around.
That said, it supports more than 10 services including  duckdns,
afraid.org, no-ip.com and dynu.com. Ip addresses to register can be
retrieved in a multitude of ways from none at all (trusting the service
provider) to the generic 'cmd' plugin which can use the output from a
command.

Dependencies
------------

Just a few:

   - python3 (tested on 3.6 and 3.4)
   - python3-straight-plugin (a. k. a. python3-straight.plugin)
   - python3-setuptools
   - The /usr/sbin/ip command is used in some plugins.

Installation
------------

**ddupdate** can be run as a regular user straight off the cloned git
directory. To make a test version possible to run from anywhere make a
symlink::

    $ ln -s $PWD/ddupdate $HOME/bin/ddupdate

It is also possible to install as a pypi package using::

    $ sudo pip install ddupdate --prefix=/usr/local

User installations are not supported, but installing in a virtual env is -
see Packaging in CONTRIBUTE.md.

Fedora and Mageia users can install binary packages from
https://copr.fedorainfracloud.org/coprs/leamas/ddupdate/.

Ubuntu users can use the PPA at
https://launchpad.net/~leamas-alec/+archive/ubuntu/ddupdate

CONTRIBUTE.md describes how to create Debian packages. Here is also more
info on using the pypi package. Overall, using native packages is the
preferred method on platforms supporting this.

Fast Track Configuration
------------------------

This is the fast track. If running into troubles, look into next
chapter Full Configuration.

Start with running *ddupdate --list-plugins services*. Pick a supported
service, check it using *ddupdate --help <service>* and register with
the relevant site. This should end up with a hostname, a user and a
secret password.

Using the info in *ddupdate --help <service>* create an entry in the
*~/.netrc* file, something like::

    machine  <service host> login <user> password <secret password>

Give it proper permissions::

    sudo chmod 600 ~/.netrc

Assuming using the ipv4 address as seen from the net, update
*/etc/ddupdate.conf* to something like::

    [update]
    address-plugin = web-default-ip
    service-plugin = <your service plugin>
    hostname = <your hostname>
    loglevel = info
    ip-version = v4

Now run *ddupdate* and check for errors.

That's the main configuration, look below for Configuring systemd


Full Configuration
------------------

Configuration is basically about selecting a plugin for a specific ddns
service and another plugin which provides the ip address to be registered.
Some plugins needs specific plugin options.

The ip plugin to use is use is normally either default-web-ip or default-if.

The *default-web-ip* plugin should be used when the address to register is
the external address visible on the internet - that is, if the registered
host should be accessed from the internet. For most services the
*ip-disabled* could be used instead. Services will then use the external
address as seen from the service. See the *ddupdate --help <service>* info.

The *default-if* plugin uses the first address found on the default
interface. This typically means registering the address used on an internal
network, and should be used if the registered host should be accessed from
the internal network.

Should these options not fit, several other ip plugins are available using
*ddupdate list ip-plugins*.  After selecting ip plugin, test it using
something like::

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dry-run
    dry-run: Using
        v4 address: 83.255.182.111
        v6 address: None
        hostname: host1.nowhere.net

After selecting the ip plugin, start the process of selecting a service
by listing all available services:

    $ ddupdate --list-plugins services
    changeip             Updates DNS data on changeip.com
    dnsexit              Updates DNS data on www.dnsexit.com
    dry-run              Debug dummy update plugin
    dtdns                Updates DNS data on dtdns.com
    duckdns              Updates DNS data on duckdns.org
    duiadns              Updates DNS data on duiadns.com
    dynu                 Updates DNS data on dynu.com
    freedns.afraid       Updates DNS data on freedns.afraid.org
    freedns.io           Updates DNS data on freedns.io
    no-ip                Updates DNS data on no-ip.com
    now-dns              Updates DNS data on now-dns.com
    system-ns            Updates DNS data on system-ns.com

Next, pick a service plugin and check the help info, here dynu::

    $ ddupdate --help dynu
    Name: dynu
    Source: /home/al/src/ddupdate/src/ddupdate/plugins/ddplugin.py

    Update a dns entry on dynu.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin.

    .netrc: Use a line like:
        machine api.dynu.com login <username> password <password>

    Options:
        none

If all looks good, register on dynu.com. This will end up in a hostname,
username and password. Using the .netrc info in the *ddupdate help
<service>*, create an entry in the *~/.netrc*  file like::

    machine api.dynu.com login <username> password <secret>

Note that this file must be protected for other users (otherwise no tools
will accept it). Do::

    $ chmod 600 ~/.netrc

Now, let's select the plugin which provides the ip address to register.
For the default case, the default-web-ip plugin generates the address as
seen from the network. Test the service using the selected ip plugin,
something like::

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dynu \
      --hostname myhost.dynu.net -L info
    INFO - Loglevel: INFO
    INFO - Using hostname: myhost.dynu.net
    INFO - Using ip address plugin: default-web-ip
    INFO - Using service plugin: dynu
    INFO - Plugin options:
    INFO - Using ip address: 90.2.18.212
    INFO - Update OK

When all is fine, update *~/.config/ddupdate.conf* or */etc/ddupdate.conf* to
something like::

    [update]
    address-plugin = web-default-ip
    service-plugin = dynu
    hostname = myhost.dynu.net
    loglevel = info

After which it should be possible to just invoke *ddupdate* without
any options.

Configuring systemd
-------------------
If using a packaged version: make your  *~/.netrc*  available for the
user running the service by copying it to the ddupdate user's home and
give it proper permissions::

    sudo cp ~/.netrc ~ddupdate
    sudo chmod 600 ~ddupdate/.netrc
    sudo chown ddupdate ~ddupdate/.netrc

systemd is used to invoke ddupdate periodically. The safest bet is
not to use the upstream systemd files. Do::

    $ sudo cp /lib/systemd/system/ddupdate* /etc/systemd/system

Check the two /etc files, in particular for paths. Test the service and
the logged info::

    $ sudo systemctl daemon-reload
    $ sudo systemcl start ddupdate.service
    $ sudo journalctl -u ddupdate.service

When all is fine make sure ddupdate is run hourly using::

    $ sudo systemctl start ddupdate.timer
    $ sudo systemctl enable ddupdate.timer

Configuring NetworkManager
--------------------------

NetworkManager can be configured to start/stop ddupdate when interfaces goes
up or down. An example script to drop in */etc/NetworkManager/dispatcher.d*
is distributed in the package.

