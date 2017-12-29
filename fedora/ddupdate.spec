%global debug_package %{nil}
#global gittag 0.0.2

%global commit b6c7add6ac4039e27c058cbdda975f59df2fe726
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           ddupdate
Version:        0.0.2
Release:        0.1.%{shortcommit}%{?dist}
Summary:        Tool updating DNS data for dynamic IP addresses

Group:          Applications/System
License:        MIT
URL:            http://github.com/leamas/ddupdate
BuildArch:      noarch
#Source0:        %{url}/archive/%{gittag}/%{name}-%{version}.tar.gz
Source0:        %{url}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz

%{?systemd_requires}

BuildRequires:  python3-devel
BuildRequires:  systemd
Requires:       python3-straight-plugin
Requires:       /usr/sbin/ip

%description
ddupdate is a tool for automatically updating dns data for a system using
e. g., DHCP. The goal is it should be possible to access a system with a
fixed dns name such as myhost.somewhere.net even if the IP  address is
changed.

From another perspective, ddupdate is a tool replicating part of the
existing ddclient functionality, but with a better overall design and user
interaction. In particular, it has better help, logging and documentation.
Thanks to the plugin design, it's also much easier to provide support for
new services and address detection strategies.

%prep
%autosetup -n %{name}-%{commit}
sed -i '/ExecStart/s|/usr/local|/usr|' systemd/ddupdate.service
sed -i '/User=/s/.*/User=ddupdate/' systemd/ddupdate.service


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
%doc README.md
%{_bindir}/ddupdate
%config(noreplace) /etc/ddupdate.conf
%{_unitdir}/ddupdate.*
%{_datadir}/ddupdate
%{_mandir}/man8/ddupdate.8*
%{python3_sitelib}/*


%changelog
* Tue Dec 26 2017 Alec Leamas <leamas.alec@gmail.com> - 0.1-0.1.95f9fd8%{?dist}
- Initial release
