Summary: Uravo.
Name: uravo
Version: 0.0.13
Release: 1
Epoch: 0
License: GPL
URL: http://www.minorimpact.com
Group: Applications/System
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildArch: noarch

Requires: perl-Net-CIDR
Requires: perl-POE
Requires: perl-DBI
Requires: perl-DBD-MySQL
Requires: perl-MIME-Lite
Requires: perl-JSON

Provides: perl(Uravo)

%description
Uravo.

%prep
%setup

%build

%install
rm -rf $RPM_BUILD_ROOT

mkdir -p ${RPM_BUILD_ROOT}
cp -r ${RPM_BUILD_DIR}/%{name}-%{version}/* ${RPM_BUILD_ROOT}/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/*

# Changelog - update this with every build of the package
%changelog
* Sun Jan 26 2014 <pgilan@minorimpact.com> 0.0.2-1
- Fixed cpu module.
- Added bandwidth module.
* Fri Jan 24 2014 <pgilan@minorimpact.com> 0.0.1-1
- Initial build.

