package Uravo::Agent::ntp;

use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Util;

my $uravo;

sub new {
    my $class = shift || return;

    my $self = {};

    $uravo = new Uravo;

    bless($self, $class);
    return $self;
}

sub run {
    my $self = shift || return;
    my $server = $uravo->getServer() || return;

    my $options = $uravo->{options};
    my $monitoringValues = $server->getMonitoringValues();

    my $message = '';
    my @clean_values = (1, 3, 7, 15, 31, 63, 127, 255);
    unless (-f "/usr/sbin/ntpq") {
        print "  /usr/sbin/ntpq is not installed\n" if ($options->{verbose});
        return;
    }

    my $cmd = "/usr/sbin/ntpq -p 2>&1 | grep LOCAL | awk '{print \$7}'";
    my $reach = `$cmd`;
    chomp($reach);
    unless ($reach) {
        $server->alert({AlertGroup=>'ntp_reach', Severity=>'red', Summary=>'Unable to collect data from ntpq.', Recurring=>1}) unless ($options->{dryrun});
        return;
    }

    my $reach_dec = oct($reach);
    my $reach_bin = $reach_dec;

    my $Severity = '';
    my $Summary = '';
    my $local = 1;
    # If we didn't get a value at all, then we've got bigger problems
    if ($reach eq '') {
        $local = 0;
        $Severity = 'red';
    }

    # Check to see if we hit a clean value
    foreach my $clean (@clean_values) {
        if ($clean == $reach_dec) {
            $Severity = 'green';
            last;
        }
    }

    # If we didn't hit a clean value, we need to count up bad checks in last 4
    my $fails = 0;
    if ($Severity eq '') {
        $Severity = 'green';
        for (my $i = 0; $i < 4; $i++) {
            if (!($reach_bin & 1)) {
                $fails++;
            }
            $reach_bin = $reach_bin >> 1;
        }
        if ($fails == 2) {
            $Severity = 'yellow';
        } elsif ($fails > 2) {
            $Severity = 'red';
        }
    }

    if ($Severity eq 'green') {
        $Summary = "NTP reachability check clean (reach: $reach)";
    } elsif (!$local) {
        $Summary = "NTP reachability check failed - no LOCAL peer found";
    } else {
        $Summary = "NTP reachability check failed $fails out of last 4 checks (reach: $reach)";
    }
    $server->alert({AlertGroup=>'ntp_reach', Severity=>$Severity, Summary=>$Summary, Recurring=>1}) unless ($options->{dryrun});


    my $ntpstat = `/usr/bin/ntpstat 2>/dev/null | grep synchronised`;
    my $severity = 'green';
    if ($ntpstat =~ /synchronised to NTP server/) {
        $Summary = "ntpstat: synchronised to NTP server";
    } elsif ($ntpstat =~ /synchronised to local net/) {
        $severity = 'red';
        $Summary = "ntpstat:synchronised to local net";
    } elsif ($ntpstat eq '') {
        $severity = 'red';
        $Summary = "no output from ntpstat";
    } else {
        $severity = 'red';
        $Summary .= "ntpstat:$ntpstat";
    }
    $server->alert({AlertGroup=>'ntp_ntpstat', Severity=>$Severity, Summary=>$Summary, Recurring=>1}) unless ($options->{dryrun});

    return;
}

1;
