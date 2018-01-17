%global gittag      0.1.0
#global commit      eb302484417d85cbf497958ba2a651f738ad7420

%global shortcommit %{?commit:%(c=%{commit}; echo ${c:0:7})}%{!?commit:%nil}
%global shortdir    %{?gittag}%{?shortcommit}
%global srcdir      %{?gittag}%{?commit}

Name:           ddupdate
Version:        0.2.1
Release:        1%{?commit:.%{shortcommit}}%{?dist}
Summary:        Tool updating DNS data for dynamic IP addresses

Group:          Applications/System
License:        MIT
URL:            http://github.com/leamas/ddupdate
BuildArch:      noarch
Source0:        %{url}/archive/%{srcdir}/%{name}-%{shortdir}.tar.gz

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  systemd
Requires(pre):  shadow-utils
Requires:       python%{python3_pkgversion}-straight-plugin
Requires:       /usr/sbin/ip

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
flexible alternative to the ubiquotious ddclient.

ddupdate is distributed with systemd support to run at regular intervals,
and with NetworkManager templates to run when interfaces goes up or down.


%prep
%autosetup -p1 -n %{name}-%{srcdir}
sed -i '/ExecStart/s|/usr/local|/usr|' systemd/ddupdate.service
sed -i '/User=/s/.*/User=ddupdate/' systemd/ddupdate.service
sed -i 's|/lib/systemd/system|%{_unitdir}|' setup.py


%build
%py3_build


%install
%py3_install
rm -rf $RPM_BUILD_ROOT%{_pkgdocdir}/*


%pre
getent group ddupdate >/dev/null || groupadd --system ddupdate
getent passwd ddupdate >/dev/null || \
    useradd --system -g ddupdate -d /var/lib/ddupdate -s /sbin/nologin \
    --create-home -c "Updates dns info for dynamic ip address" ddupdate

%post
%systemd_post ddupdate.timer

%preun
%systemd_preun ddupdate.timer

%postun
%systemd_postun_with_restart ddupdate.timer


%files
%license LICENSE.txt
%doc README.md NEWS CONTRIBUTE.md
%{_bindir}/ddupdate
%config(noreplace) /etc/ddupdate.conf
%{_unitdir}/ddupdate.*
%{_datadir}/ddupdate
%{_mandir}/man8/ddupdate.8*
%{python3_sitelib}/*


%changelog
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
