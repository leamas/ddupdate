ddupdate - update dns data for dynamic ip addresses.
====================================================

General
-------

ddupdate is a tool for automatically updating dns data for a system using
for example  DHCP. The goal is it should be possible to access a system with
a fixed dns name such as myhost.somewhere.net even if the IP address is
changed. Another goal is tp provide a flexible, user-friendly, maintainable
and linux-centric alternative to the ubiquitous ddclient.


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

   - python3 (tested on 3.6)
   - python3-straight-plugin
   - python3-setuptools
   - The /usr/sbin/ip command is used in some plugins.

Installation
------------

**ddupdate** can be run as a regular user straight off the cloned git
directory. To make a test version possible to run from anywhere make a
symlink::

    $ ln -s $PWD/ddupdate $HOME/bin/ddupdate

User installations are not supported. To make a local site installation
in /usr/local run something like::

    $ sudo python3 setup.py --prefix=/usr/local

**ddupdate** can be installed in an virtualenv root by a regular user. To
use the plugins in the venv in favor of the system ones prepend the proper
path to XDG\_DATA\_DIRS using something like::

    $ export  XDG_DATA_DIRS=$PWD/share:$XDG_DATA_DIRS

See Packaging below for building proper native packages for Debian and
Fedora. This is the preferred installation method on these platforms.

Fast Track Configuration
------------------------
This is the fast track. When running into troubles, look into next
chapter Full Configuration.

Start with running *ddupdate --list-plugins services*. Pick a supported
service, check it using *ddupdate --help <service>* and register on
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
    service-plugin = <<your service plugin>
    hostname = <your hostname>
    loglevel = info

Now run *ddupdate* and check for errors.

That's the main configuration, look below for Configuring systemd


Full Configuration
------------------

Configuration is basically about selecting a plugin for a specific ddns
service and possibly another plugin which provides the ip address to be
registered. Some plugins needs specific plugin options.

First question is what kind of ip address which should be registered. The
most common case is to use the address as seen from the internet to make
it possible for users on internet to access the machine.

Another case is when using DHCP addresses on an internal network behind
a router and the machine should be reached by users on this network.
In this case the machine's real address should be registered.

In any case, begin with listing all plugins::

    $ ddupdate --list-plugins ip-plugins
    ip-disabled          Force update service to provide ip address
    ip-from-command      Obtain address from a command
    default-if           Get ip address from default interface (linux)
    default-web-ip       Obtain external address as seen from the net
    hardcoded-if         Get address from a configuration option
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
    Source: /home/al/src/ddupdate/src/ddupdate/plugins/plugins_base.py

    Update a dns entry on dynu.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin.

    .netrc: Use a line like:
        machine api.dynu.com login <username> password <password>

    Options:
        none

If all looks good, register on dynu.com. This will end up in a hostname,
username and password. Create an entry in the *~/.netrc*  file like::

    machine api.dynu.com login <username> password <secret>

Note that this file must be protected for other users (otherwise no tools
will accept it). Do::

    $ chmod 600 ~/.netrc

Now, let's select the plugin which provides the ip address to register.
For the default case, the default-web-ip plugin generates the address as
seen from the network. This can be tested using::

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dry-run
    dry-run: Using address 90.224.208.212 and hostname host.nowhere.net

All looks good. Now, let's try to actually update that hostname on dynu.com::

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dynu \
      --hostname myhost.dynu.net -L info
    INFO - Loglevel: INFO
    INFO - Using hostname: myhost.dynu.net
    INFO - Using ip address plugin: default-web-ip
    INFO - Using service plugin: dynu
    INFO - Plugin options:
    INFO - Using ip address: 90.224.208.212
    INFO - Update OK

Again fine. Update *~/.config/ddupdate.conf* or */etc/ddupdate.conf* to
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

    sudo cp ~/.netrc /var/lib/ddupdate
    sudo chmod 600 /var/lib/ddupdate/.netrc
    sudo chown ddupdate /var/lib/ddupdate/.netrc

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

Packaging
---------

ddupdate has a multitude of packaging:

   - ddupdate is available as a **pypi package** from the master branch. It
     can be installed using pip::

         $ sudo pip install ddupdate --prefix=/usr

   - **fedora** is packaged in the *fedora* branch.  Pre-built packages are
     at https://copr.fedorainfracloud.org/coprs/leamas/ddupdate/ Building
     requires the fedora toolchain in the *git*, *rpmdevtools* and
     *rpm-build* packages.  To build::

         $ git clone -b fedora https://github.com/leamas/ddupdate.git
         $ cd ddupdate
         $ spectool -g ddupdate.spec
         $ rpmbuild -D "_sourcedir $PWD" -ba ddupdate.spec

     This creates both a source and a binary rpm package underneath *rpmbuild*.

   - The **debian** packaging is based on gbp and lives in the *debian* and
     *pristine-tar* branches.  The packages *git-buildpackage*, *devscripts*
     and *git*  are required to build. To build current version 0.0.6 do::

         $ git clone -b debian https://github.com/leamas/ddupdate.git
         $ cd ddupdate
         $ gbp buildpackage --git-upstream-tag=0.0.6.
         $ git clean -fd    # To be able to rebuild

Writing plugins
---------------

Writing plugins is not hard. Most plugins are about 10-20 lines of code +
docs, most of which boilerplate stuff. The best way is to look at the
existing plugins and pick solutions from them. Some hints:

  - Before writing the plugin, make tests with wget or curl to make
    sure how the api works. Essential step, this one.

  - Each plugin must contain a main class derived from IpPlugin or
    UpdatePlugin. The class docstring is the *help <plugin>* documentation.

  - The class ```_name``` property is the official name of the plugin, must
    be unique. ```_oneliner``` is indeed the short summary displayed by
    *--list-plugins*.

  - Authentication:
      - Some sites uses standard basic authentication. This is handled
        by *http_basic_auth_setup* e. g., ```no_ip.py```
      - Others uses username + password in the url e. g., ```dnsexit.py```
      - Other uses hashed passwords, e. g., ```dynu.py```
      - API tokens are handled in e. g., ```duckdns.py```
      - Some have broken basic authentication, see ```now_dns.py```
  - Most services uses a http GET request to set the data. See
    ```freedns_io.py``` for a http POST example.
  - Reply decoding:
      - Most sites just returns some text, simple enough
      - json: example in ```system_ns.py```
      - html: example in ```duiadns.py```
