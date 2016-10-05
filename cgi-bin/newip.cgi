#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $server_id = $form->{server_id};
    my $network = $form->{network};
    my $server = $uravo->getServer($server_id) || die("Can't get server object.");

    print "Content-type: text/html\n\n";

    if ($server && $network) {
        #my ($octet2, $octet3, $octet4) = $NETWORK->get_new_octets_from_version_4_hostname($server_id, $interface); 
        #print "10.$octet2.$octet3.$octet4";
        print $server->newip($network); 
    }
}

