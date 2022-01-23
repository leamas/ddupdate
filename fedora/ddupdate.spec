%global __python __python3

%global gittag      0.6.6
#global commit      eb302484417d85cbf497958ba2a651f738ad7420

%global shortcommit %{?commit:%(c=%{commit}; echo ${c:0:7})}%{!?commit:%nil}
%global shortdir    %{?gittag}%{?shortcommit}
%global srcdir      %{?gittag}%{?commit}

# mageia 6- fix:
%{!?_userunitdir: %global _userunitdir /usr/lib/systemd/system}

#Suse fix:
%{!?python3_pkgversion:%global python3_pkgversion 3}

Name:           ddupdate
Version:        0.6.6
Release:        1%{?dist}
Summary:        Tool updating DNS data for dynamic IP addresses

Group:          Applications/System
License:        MIT
URL:            http://github.com/leamas/ddupdate
BuildArch:      noarch
Source0:        %{url}/archive/%{srcdir}/%{name}-%{shortdir}.tar.gz

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  /usr/bin/pkg-config
BuildRequires:  systemd

Requires:       /usr/sbin/ip
Recommends:     python3-requests

%{?systemd_requires}

%description

A tool to update dynamic IP addresses typically obtained using DHCP
with dynamic DNS services such as changeip.com, duckdns.org or no-ip.com.
It makes it  possible to access a machine with a fixed name like
myhost.duckdns.org even if the ip address changes. ddupdate caches the
address, and only attempts the update if the address actually is changed.

The tool has a plugin structure with plugins for obtaining the actual
address (typically hardware-dependent) and to update it (service depen‐
dent). For supported services, it's a linux-centric, user-friendly and
flexible alternative to the ubiquitous ddclient.

ddupdate is distributed with systemd support to run at regular intervals,
and with NetworkManager templates to run when interfaces goes up or down.


%prep
%autosetup -p1 -n %{name}-%{srcdir}
sed -i '/ExecStart/s|/usr/local|/usr|' systemd/ddupdate.service
sed -i '/glob/s|systemd_unitdir()|"lib/systemd/user"|' setup.py


%build
%py3_build


%install
%py3_install
%py_byte_compile %{__python3} %{buildroot}%{_datadir}/ddupdate/plugins

# Remove BUILDROOT prefix in installation paths in install.conf
sed -i  's|\([^=]*= \).*BUILDROOT/[^/]*|\1|' \
    %{buildroot}%{python3_sitelib}/ddupdate/install.conf


%files
%license LICENSE.txt
%doc README.md NEWS CONTRIBUTE.md CONFIGURATION.md
%{_bindir}/ddupdate
%{_bindir}/ddupdate-config
%{_userunitdir}/ddupdate*
%{_datadir}/ddupdate
%{_datadir}/bash-completion/completions/ddupdate
%{_mandir}/man8/ddupdate.8*
%{_mandir}/man8/ddupdate-config.8*
%{_mandir}/man5/ddupdate.conf.5*
%{python3_sitelib}/*


%changelog
* Thu Jan 20 2022 Alec Leamas <leamas.alec@nowhere.net> - 0.6.6-1
- New upstream version
- Fix bad installation paths (upstream #54)

* Fri Jun 12 2020 Alec Leamas <leamas.alec@nowhere.net> - 0.6.5-1
- New upstream version

* Sun Jul 07 2019 Alec Leamas <leamas.alec@gmail.com> - 0.6.4-2
- Fix mageia builds (define %%_userunitdir)

* Sun Jul 07 2019 Alec Leamas <leamas.alec@gmail.com> - 0.6.4-1
- New upstream version

* Fri Jun 07 2019 Alec Leamas <leamas.alec@gmail.com> - 0.6.3-1
- New upstream release.
- Dropped patch now in upstream.

* Fri Jun 07 2019 Alec Leamas <leamas.alec@gmail.com> - 0.6.2-2
- Fx upstream bug #21, broken ipv6 config file parsing.

* Mon Feb 18 2019 Alec Leamas <leamas.alec@gmail.com> - 0.6.2-1
- New upstream version.

* Tue Jun 12 2018 Alec Leamas <leamas.alec@gmail.com> - 0.6.1-1
- New upstream maintenance release

* Sun Feb 18 2018 Alec Leamas <leamas.alec@gmail.com> - 0.6.0-1
- New upstream release
- Drop system-wide systemd services and config files.

* Thu Feb 08 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.3-2
- Add upstream patch: Documentation stanzas added to systemd units.

* Sun Feb 04 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.3-1
- New upstream release
- Drop upstream patches
- New documentation installation scheme.

* Sat Feb 03 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.2-5
- Fix horrible bug in patch for ddupdate-config in -4

* Sat Feb 03 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.2-4
- Update patch from -2
- New patches fixed ddupdate-config bugs

* Fri Feb 02 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.2-3
- Fix plugins being bytecompiled using python 2.7

* Thu Feb 01 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.2-2
- Add upstream patch removing straight.plugin dependency.

* Sun Jan 28 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.2-1
- New upstream release
- Patches dropped

* Sat Jan 27 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.1-2
- Add upstream patch for bash completions install path
- Add upstream patch for missing list-addressers/services completions

* Sat Jan 27 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.1-1
- New upstream release

* Wed Jan 24 2018 Alec Leamas <leamas.alec@gmail.com> - 0.5.0-1
- New upstream version.
- New tool ddupdate-config and new manpages.

* Sun Jan 21 2018 Alec Leamas <leamas.alec@gmail.com> - 0.4.1-1
- New upstream release.

* Sat Jan 20 2018 Alec Leamas <leamas.alec@gmail.com> - 0.4.0-1
- New upstream release.

* Thu Jan 18 2018 Alec Leamas <leamas.alec@gmail.com> - 0.3.0-1
- New upstream release

* Wed Jan 17 2018 Alec Leamas <leamas.alec@gmail.com> - 0.2.1-2
- Fix FTBS on epel builders

* Wed Jan 17 2018 Alec Leamas <leamas.alec@gmail.com> - 0.2.1-1
- New upstream release.

* Sat Jan 13 2018 Alec Leamas <leamas.alec@gmail.com> - 0.2.0-1
- New upstream release.

* Mon Jan 08 2018 Alec Leamas <leamas.alec@gmail.com> - 0.1.0-3
- Review remarks: Use %%{_unitdir}, %%py3_install, skip debug_package nil

* Sun Jan 07 2018 Alec Leamas <leamas.alec@gmail.com> - 0.1.0-2
- Fix unpackaged document file.

* Sun Jan 07 2018 Alec Leamas <leamas.alec@gmail.com> - 0.1.0-1
- New upstream release

* Thu Jan 04 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.6-3
- NetworkManager support patch, from upstream

* Thu Jan 04 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.6-2
- Fix epel-7 build error

* Wed Jan 03 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.6-1
- New upstream release.

* Wed Jan 03 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.5-0.6.eb30248
- rebuilt

* Tue Jan 02 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.5-0.5.rc2
- Published on COPR.
- Fix version-release
- Fix python version references.

* Tue Jan 02 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.5rc2-0.4
- New upstream release

* Tue Jan 02 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.5rc1-0.1
- New upstream release

* Fri Dec 29 2017 Alec Leamas <leamas.alec@gmail.com> - 0.0.2-0.2
- New upstream release, initial install testing done.

* Tue Dec 26 2017 Alec Leamas <leamas.alec@gmail.com> - 0.1-0.1.95f9fd8%{?dist}
- Initial release
