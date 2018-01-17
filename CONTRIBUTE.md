This document is both some upstream notes and an introduction to
maintaining ddupdate code.

Writing plugins
---------------

Writing plugins is not hard. Most plugins are about 10-20 lines of code +
docs, most of which boilerplate stuff. The best way is to look at the
existing plugins and pick solutions from them. Some hints:

  - Before writing the plugin, make tests with wget or curl to make
    sure how the api works. Essential step, this one.

  - The plugin API is defined in the plugins\_base.py file. API docs can be
    generated using *python3 -m pydoc lib/ddupdate/ddplugin.py* or so.

  - Each plugin must live in a file with a unique name. It must contain a
    main class derived from IpPlugin or UpdatePlugin. The class docstring
    is the *help <plugin>* documentation.

  - The class ```_name``` property is the official name of the plugin, must
    be unique. ```_oneliner``` is indeed the short summary displayed by
    *--list-plugins*.

  - Authentication:
      - Some sites uses standard basic authentication. This is handled
        by *http_basic_auth_setup* in e. g., ```no_ip.py```
      - Others uses username + password in the url e. g., ```dnsexit.py```
      - Hashed passwords are used in e. g., ```dynu.py```
      - API tokens are handled in e. g., ```duckdns.py```
      - Some have broken basic authentication, see ```now_dns.py```

  - Most services uses a http GET request to set the data. See
    ```freedns_io.py``` for a http POST example.

  - Reply decoding:
      - Most sites just returns some text, simple enough
      - json: example in ```system_ns.py```
      - html: example in ```duiadns.py```

Creating a new version
----------------------

  - Replace all occurrences of version string:

        sed -E -i 's/([^\.])0\.[0-9]+\.[0-9]+([^\. ])/\10.1.0\2/' $(git ls-files

  - Update NEWS file.

  - Tag the release: git tag 0.1.0

  - Create fedora package:

        git checkout fedora
        cd fedora
        ./make-tarball 0.1.0
        rpmdev-bumpspec *.spec , and edit it.
        rm -rf rpmbuild
        rpmbuild-here -ba *.spec

  - Copy tarball and repo to debian and commit it on pristine-tar

        git fetch upstream pristine-tar:pristine-tar
        git fetch upstream debian:debian
        scp fedora/ddupdate-0.1.0.tar.gz sid:
        cd ..; ssh sid rm -rf ddupdate.git
        scp -rq ddupdate sid:ddupdate.git
        ssh sid
        cd ddupdate; rm  -rf *
        mv ../ddupdate-0.1.0.tar.gz ddupdate_0.1.0.orig.tar.gz
        git clone -o upstream -b debian ../ddupdate.git ddupdate
        cd ddupdate
        git fetch upstream pristine-tar:pristine-tar
        pristine-tar commit ../ddupdate_0.1.0.orig.tar.gz 0.1.0

  - Upload to pypi:

        python3 setup.py sdist upload

  - Create debian  test huild on sid:
        $ cd ddupdate/ddupdate
        $ sudo mk-build-deps -i -r  debian/control
        $ git fetch upstream pristine-tar:pristine-tar
        $ git merge -X theirs 0.1.0 --allow
        $ cd ..; tar xf ddupdate_0.1.0.orig.tar.gz
        $ diff -r ddupdate-0.1.0 ddupdate > foo
        # Remove all cruft left in foo after merge.
        $ git commit -am "new upstream release..."
        $ git  clean -fd
        $ gbp buildpackage --git-upstream-tag=0.1.0 -us -uc
        $ git clean -fd; git checkout .    # To be able to rebuild

  - Create fedora packages (README.md)
  - Make a new COPR build
  - Create an Ubuntu package (TBD)
    - Needs tar >= 1.29b, pristine-tar >= 1.42 (from zesty)
    - sudo ntpdate se.pool.ntp.org
    - git clone -o upstream -b debian https://github.com/leamas/ddupdate.git
    - git fetch upstream pristine-tar:pristine-tar
    - pristine-tar checkout ddupdate\_0.1.0.orig.tar.gz
    - mv ddupdate\_0.1.0.orig.tar.gz ..
    - sudo mk-build-deps -i -r debian/control
    - Edit debian/changelog, add ~ubuntu1 suffix, change Standard-version
      -> 3.9.7
    - debuild -S
    - dput ppa:leamas-alec/ddupdate ../ddupdate\*source.changes

Packaging
---------

ddupdate has a multitude of packaging:

  - ddupdate is available as a **pypi package** from the master branch. It
    can be installed using pip::

        $ sudo pip install ddupdate --prefix=/usr/local

    or from the cloned git directory:

        $ sudo python3 setup.py install --prefix=/usr/local

    It can be installed in an virtualenv root by a regular user. To use
    the plugins in the venv in favor of the system ones prepend the proper
    path to XDG\_DATA\_DIRS using something like::

        $ export  XDG_DATA_DIRS=$PWD/share:$XDG_DATA_DIRS

    Using a virtualenv, configuration files like */etc/ddupdate.conf* and
    *~/.netrc* are still used from their system-wide locations.

  - **fedora** is packaged in the *fedora* branch.  Pre-built packages are
    at https://copr.fedorainfracloud.org/coprs/leamas/ddupdate/. Building
    requires the *git* and *rpm-build* packages. To build version 0.2.1::

        $ git clone -b fedora https://github.com/leamas/ddupdate.git
        $ cd ddupdate/fedora
        $ sudo dnf builddep ddupdate.spec
        $ ./make-tarball0.1.0
        $ rpmbuild -D "_sourcedir $PWD" -ba ddupdate.spec
        $ rpm -U --force rpmbuild/RPMS/noarch/ddupdate*rpm

  - The **debian** packaging is based on gbp and lives in the *debian* and
    *pristine-tar* branches.  The packages *git-buildpackage*, *devscripts*
    and *git*  are required to build. To build current version0.1.0 do::

        $ mkdir ddupdate; cd ddupdate
        $ git clone -o upstream -b debian https://github.com/leamas/ddupdate.git
        $ cd ddupdate
        $ sudo mk-build-deps -i -r  debian/control
        $ git fetch upstream pristine-tar:pristine-tar
        $ gbp buildpackage --git-upstream-tag0.1.0 -us -uc
        $ git clean -fd; git checkout .    # To be able to rebuild
        $ dpkg -i ../ddupdate0.2.1*_all.deb
