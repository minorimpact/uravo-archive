package Uravo::Agent::conn;

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Time::HiRes;
use Net::Ping;

my $uravo;
my $conn;
my $PING;

sub new {
    my $class = shift || return;

    if ($conn) {
        return $conn;
    }

    $conn ||= bless({}, $class);
    $uravo ||= new Uravo;
    $PING ||= Net::Ping->new("icmp", 1, 56);
    $PING->hires();

    return $conn;
}

sub run {
    my $self = shift || return;
    my $server = shift || return;
    my $server_id = $server->id();

    my $options = $uravo->{options};
    my $local_server = $uravo->getServer();

    foreach my $interface ($server->getInterfaces({icmp=>1})) {
        my $ping_target = $interface->get('ip');
        next unless ($ping_target =~/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/);
        my ($ret, $duration, $ip) = $PING->ping($ping_target);
        $duration = sprintf("%.3f", $duration);
        if ($ret) {
            my $Summary = "$server_id ($ping_target) responded to ping in $duration seconds";
            $server->alert({AlertGroup=>'conn', AlertKey=>$ping_target, Severity=>'green', Summary=>$Summary});
            $server->graph('conn', $duration);
        } else {
            my $Summary = "$server_id ($ping_target) is not responding to ping";
            $server->alert({AlertGroup=>'conn', AlertKey=>$ping_target,  Severity=>'red', Summary=>$Summary});
        }
    }
}

1;

