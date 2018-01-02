%global debug_package %{nil}
%global gittag 0.0.5rc1

%global commit 0489e0280b58a868d73a3ddd451d239b3c035d7b
#global shortcommit %%(c=%%{commit}; echo ${c:0:7})

Name:           ddupdate
Version:        0.0.5rc1
Release:        0.3%{?shortcommit:.}%{?shortcommit}%{?dist}
Summary:        Tool updating DNS data for dynamic IP addresses

Group:          Applications/System
License:        MIT
URL:            http://github.com/leamas/ddupdate
BuildArch:      noarch
Source0:        %{url}/archive/%{gittag}/%{name}-%{version}.tar.gz
#Source0:       %%{url}/archive/%%{commit}/%%{name}-%%{shortcommit}.tar.gz

%{?systemd_requires}

BuildRequires:  python3-devel
BuildRequires:  systemd
Requires:       python3-straight-plugin
Requires:       /usr/sbin/ip

%description

A tool to update dynamic IP addresses typically obtained using DHCP
at dynamic DNS services such as changeip.com, duckdns.org no-ip.com.
The goal is that it should be possible to access a machine with a fixed
name like myhost.duckdns.org even if the ip address changes. ddupdate
caches the address, and only attempts the update if the address actu‐
ally is changed.

The tool has a plugin structure with plugins for obtaining the actual
address (typically hardware-dependent) and to update it (service depen‐
dent). For supported services, it's a linux-centric, user-friendly and
flexible alternative to the uiquotious ddclient.

ddupdate is distributed with systemd support to run at regular intervals,
and with NetworkManager templates to run when interfaces goes up or down.

%prep
%autosetup -n %{name}-%{version}
sed -i '/ExecStart/s|/usr/local|/usr|' systemd/ddupdate.service
sed -i '/User=/s/.*/User=ddupdate/' systemd/ddupdate.service
cp README.md README.rst


%build


%install
python3 setup.py install --root=$RPM_BUILD_ROOT --prefix=/usr
mkdir -p $RPM_BUILD_ROOT/usr/lib/systemd/system
mv $RPM_BUILD_ROOT/lib/systemd/system/* $RPM_BUILD_ROOT/usr/lib/systemd/system
rm  $RPM_BUILD_ROOT/usr/share/doc/ddupdate/LICENSE.txt
rm  $RPM_BUILD_ROOT/usr/share/doc/ddupdate/ddupdate.8.html

%pre
getent group ddupdate >/dev/null || groupadd -r ddupdate
getent passwd ddupdate >/dev/null || \
    useradd -r -g ddupdate -d /var/lib/ddupdate -s /sbin/nologin \
    -c "Updates dns info for dynamic ip address" ddupdate
test -d /var/lib/ddupdate || {
    mkdir /var/lib/ddupdate
    chown ddupdate:ddupdate /var/lib/ddupdate
    chmod 600 /var/lib/ddupdate
}

%post
%systemd_post ddupdate.timer

%preun
%systemd_preun ddupdate.timer

%postun
%systemd_postun_with_restart ddupdate.timer


%files
%license LICENSE.txt
%doc README.md README.rst NEWS
%{_bindir}/ddupdate
%config(noreplace) /etc/ddupdate.conf
%{_unitdir}/ddupdate.*
%{_datadir}/ddupdate
%{_mandir}/man8/ddupdate.8*
%{python3_sitelib}/*


%changelog
* Tue Jan 02 2018 Alec Leamas <leamas.alec@gmail.com> - 0.0.5rc1-0.1
- New upstream release

* Fri Dec 29 2017 Alec Leamas <leamas.alec@gmail.com> - 0.0.2-0.2
- New upstream release, initial install testing done.

* Tue Dec 26 2017 Alec Leamas <leamas.alec@gmail.com> - 0.1-0.1.95f9fd8%{?dist}
- Initial release
