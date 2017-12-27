%global debug_package %{nil}
%global gittag 0.1

%global commit 95f9fd84aeb6edb5ea92d0f0b1e4c8581d1232bb
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           ddupdate
Version:        0.1
Release:        0.1.%{shortcommit}%{?dist}
Summary:        Tool updating DNS data for dynamic IP addresses

Group:          Applications/System
License:        MIT
URL:            http://github.com/leamas/ddupdate
BuildArch:      noarch
Source0:        %{url}/archive/%{gittag}/%{name}-%{version}.tar.gz
#Source0:        %%{url}/archive/%%{commit}/%%{name}-%%{shortcommit}.tar.gz

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
%autosetup -n %{name}-%{version}


%build


%install
python3 setup.py install --root=$RPM_BUILD_ROOT --prefix=/usr
mkdir -p $RPM_BUILD_ROOT/usr/lib/systemd/system
mv $RPM_BUILD_ROOT/lib/systemd/system/* $RPM_BUILD_ROOT/usr/lib/systemd/system
rm  $RPM_BUILD_ROOT/usr/share/doc/ddupdate/COPYING
rm  $RPM_BUILD_ROOT/usr/share/doc/ddupdate/ddupdate.8.html


%post
%systemd_post ddupdate.timer

%preun
%systemd_preun ddupdate.timer

%postun
%systemd_postun_with_restart ddupdate.timer


%files
%license COPYING
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
