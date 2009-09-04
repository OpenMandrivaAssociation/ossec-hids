%define _localstatedir %{_var}
%define prg  ossec

Name:        ossec-hids
Version:     1.4
Release:     %mkrel 4
Summary:     Host-based Intrusion Detection System
License:     GPLv2+
Group:       Monitoring
URL:         http://www.ossec.net/
Source0:     http://www.ossec.net/files/ossec-hids-%{version}.tar.gz
Source2:     %{name}.init
Source3:     asl_rules.xml
Source4:     authpsa_rules.xml
Patch0:      %{name}-build.patch
Patch1:      ossec-server-config.patch
Patch2:      decoder-asl.patch
Patch3:      syslog_rules.patch
Patch4:      ossec-client-conf.patch
Patch5:      firewall-drop-update.patch
Provides:    %{name}.pp = %{version}-%{release}
Provides:    ossec = %{version}-%{release}
Requires(pre):  rpm-helper
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(postun): rpm-helper
BuildRequires: apache-devel
BuildRequires: openssl-devel
BuildRoot:   %{_tmppath}/%{name}-%{version}-%{release}-root

%description
OSSEC HIDS is an Open Source Host-based Intrusion Detection
System. It performs log analysis, integrity checking, rootkit
detection, time-based alerting and active response.

%package client
Summary:     The OSSEC HIDS Client
Group:       Monitoring
Provides:    %{name}-client.pp = %{version}-%{release}
Provides:    ossec-client = %{version}-%{release}
Requires:    %{name} = %{version}-%{release}
Requires:    %{name}.pp = %{version}-%{release}
Requires(pre):  rpm-helper
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(postun): rpm-helper
Conflicts:   %{name}-server <= %{version}-%{release}

%description client
The %{name}-client package contains the client part of the
OSSEC HIDS. Install this package on every client to be
monitored.

%package server
Summary:     The OSSEC HIDS Server
Group:       Monitoring
Provides:    %{name}-server.pp = %{version}-%{release}
Provides:    ossec-server = %{version}-%{release}
Requires:    %{name} = %{version}-%{release}
Requires:    %{name}.pp = %{version}-%{release}
Requires(pre):  rpm-helper
Requires(post): rpm-helper
Requires(preun): rpm-helper
Requires(postun): rpm-helper
Conflicts:   %{name}-client <= %{version}-%{release}

%description server
The %{name}-server package contains the server part of the
OSSEC HIDS. Install this package on a central machine for
log collection and alerting.

%prep
%setup -q
%patch0 -p1
%patch1 -p0
%patch2 -p0
%patch3 -p0
%patch4 -p0
%patch5 -p0

# Prepare for docs
rm -rf contrib/specs
chmod -x contrib/*

%build
pushd src
%make all
%make build
popd

%install
rm -rf ${RPM_BUILD_ROOT}

mkdir -p ${RPM_BUILD_ROOT}%{_initrddir}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/{bin,stats,rules,tmp}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/logs/{archives,alerts,firewall}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/queue/{alerts,%{prg},fts,syscheck,rootcheck,agent-info,rids}
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/var/run
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/etc/shared
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/active-response/bin

# Generate the ossec-init.conf template
echo "DIRECTORY=\"%{_localstatedir}/lib/%{prg}\"" >  %{prg}-init.conf
echo "VERSION=\"%{version}\""                 >> %{prg}-init.conf
echo "DATE=\"`date`\""                        >> %{prg}-init.conf

install -m 0600 %{prg}-init.conf ${RPM_BUILD_ROOT}%{_sysconfdir}
install -m 0644 etc/%{prg}.conf ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/etc/%{prg}.conf.sample
install -m 0644 etc/%{prg}-{agent,server}.conf ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/etc
install -m 0644 etc/*.xml ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/etc
install -m 0644 etc/internal_options* ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/etc
install -m 0644 etc/rules/* ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/rules
install -m 0644 %{SOURCE3} ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/rules
install -m 0550 bin/* ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/bin
install -m 0755 active-response/*.sh ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/active-response/bin
install -m 0644 src/rootcheck/db/*.txt ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/etc/shared

install -m 0755 %{SOURCE2} ${RPM_BUILD_ROOT}%{_initrddir}/%{name}
install -m 0550 src/init/%{prg}-{client,server}.sh ${RPM_BUILD_ROOT}%{_localstatedir}/lib/%{prg}/bin

cp -fpL %{_sysconfdir}/localtime %{buildroot}%{_localstatedir}/lib/%{prg}/etc

%clean
rm -rf ${RPM_BUILD_ROOT}

%pre
%_pre_useradd %{prg} %{_localstatedir}/lib/%{prg} /sbin/nologin

%pre server
%_pre_useradd %{prg}m %{_localstatedir}/lib/%{prg} /sbin/nologin
%_pre_useradd %{prg}e %{_localstatedir}/lib/%{prg} /sbin/nologin
%_pre_useradd %{prg}r %{_localstatedir}/lib/%{prg} /sbin/nologin

%post client
echo "TYPE=\"agent\"" >> %{_sysconfdir}/%{prg}-init.conf

if [ ! -f  %{_localstatedir}/lib/%{prg}/etc/%{prg}.conf ]; then
  ln -sf %{prg}-agent.conf %{_localstatedir}/lib/%{prg}/etc/%{prg}.conf
fi

ln -sf %{prg}-client.sh %{_localstatedir}/lib/%{prg}/bin/%{prg}-control

touch %{_localstatedir}/lib/%{prg}/logs/ossec.log
chown %{prg}:%{prg} %{_localstatedir}/lib/%{prg}/logs/ossec.log
chmod 0664 %{_localstatedir}/lib/%{prg}/logs/ossec.log

%_post_service %{name}

%post server
echo "TYPE=\"server\"" >> %{_sysconfdir}/%{prg}-init.conf

if [ ! -f %{_localstatedir}/lib/%{prg}/etc/%{prg}.conf ]; then
  ln -sf %{prg}-server.conf %{_localstatedir}/lib/%{prg}/etc/%{prg}.conf
fi

ln -sf %{prg}-server.sh %{_localstatedir}/lib/%{prg}/bin/%{prg}-control

touch %{_localstatedir}/lib/%{prg}/logs/ossec.log
chown %{prg}:%{prg} %{_localstatedir}/lib/%{prg}/logs/ossec.log
chmod 0664 %{_localstatedir}/lib/%{prg}/logs/ossec.log

%_post_service %{name}

%preun client
if [ $1 = 0 ]; then
  %_preun_service %{name}

  rm -f %{_localstatedir}/lib/%{prg}/etc/localtime
  rm -f %{_localstatedir}/lib/%{prg}/etc/%{prg}.conf
  rm -f %{_localstatedir}/lib/%{prg}/bin/%{prg}-control
fi

%preun server
if [ $1 = 0 ]; then
  %_preun_service %{name}

  rm -f %{_localstatedir}/lib/%{prg}/etc/localtime
  rm -f %{_localstatedir}/lib/%{prg}/etc/%{prg}.conf
  rm -f %{_localstatedir}/lib/%{prg}/bin/%{prg}-control
fi

%files
%defattr(0644,root,root,0755)
%doc BUGS CONFIG CONTRIB INSTALL* README
%doc %dir contrib doc
%defattr(-,root,root,0755)
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/active-response
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/active-response/bin
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/bin
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/etc
%attr(770,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/etc/shared
%attr(750,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/logs
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue
%attr(770,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/alerts
%attr(770,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/%{prg}
%attr(750,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/syscheck
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/var
%attr(770,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/var/run

%files client
%defattr(-,root,root)
#%attr(600,root,root) %verify(not md5 size mtime) %{_sysconfdir}/%{prg}-init.conf
%attr(600,root,root) %config(noreplace) %{_sysconfdir}/%{prg}-init.conf
%{_initrddir}/*
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/%{prg}-agent.conf
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/internal_options*
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/shared/*
%{_localstatedir}/lib/%{prg}/etc/*.sample
%{_localstatedir}/lib/%{prg}/active-response/bin/*
%{_localstatedir}/lib/%{prg}/bin/%{prg}-client.sh
%{_localstatedir}/lib/%{prg}/bin/%{prg}-agentd
%{_localstatedir}/lib/%{prg}/bin/%{prg}-logcollector
%{_localstatedir}/lib/%{prg}/bin/%{prg}-syscheckd
%{_localstatedir}/lib/%{prg}/bin/%{prg}-execd
%{_localstatedir}/lib/%{prg}/bin/manage_client
%attr(755,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/rids

%files server
%defattr(-,root,root)
#%attr(600,root,root) %verify(not md5 size mtime) %{_sysconfdir}/%{prg}-init.conf
%attr(600,root,root) %config(noreplace) %{_sysconfdir}/%{prg}-init.conf
%{_initrddir}/*
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/%{prg}-server.conf
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/internal_options*
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/*.xml
%config(noreplace) %{_localstatedir}/lib/%{prg}/etc/shared/*
%{_localstatedir}/lib/%{prg}/etc/*.sample
%{_localstatedir}/lib/%{prg}/etc/localtime
%{_localstatedir}/lib/%{prg}/active-response/bin/*
%{_localstatedir}/lib/%{prg}/bin/%{prg}-server.sh
%{_localstatedir}/lib/%{prg}/bin/%{prg}-agentd
%{_localstatedir}/lib/%{prg}/bin/%{prg}-analysisd
%{_localstatedir}/lib/%{prg}/bin/%{prg}-execd
%{_localstatedir}/lib/%{prg}/bin/%{prg}-logcollector
%{_localstatedir}/lib/%{prg}/bin/%{prg}-maild
%{_localstatedir}/lib/%{prg}/bin/%{prg}-monitord
%{_localstatedir}/lib/%{prg}/bin/%{prg}-remoted
%{_localstatedir}/lib/%{prg}/bin/%{prg}-syscheckd
%{_localstatedir}/lib/%{prg}/bin/%{prg}-dbd
%{_localstatedir}/lib/%{prg}/bin/list_agents
%{_localstatedir}/lib/%{prg}/bin/manage_agents
%{_localstatedir}/lib/%{prg}/bin/syscheck_update
%{_localstatedir}/lib/%{prg}/bin/clear_stats
%attr(750,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/logs/archives
%attr(750,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/logs/alerts
%attr(750,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/logs/firewall
%attr(755,%{prg}r,%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/agent-info
%attr(755,%{prg}r,%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/rids
%attr(700,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/fts
%attr(700,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/queue/rootcheck
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/rules
%config(noreplace) %{_localstatedir}/lib/%{prg}/rules/*
#%config %{_localstatedir}/lib/%{prg}/rules/*
%attr(750,%{prg},%{prg}) %dir %{_localstatedir}/lib/%{prg}/stats
%attr(550,root,%{prg}) %dir %{_localstatedir}/lib/%{prg}/tmp

