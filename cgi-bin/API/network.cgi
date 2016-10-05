#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use JSON;
use CGI;

&main(); 

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;


    print "Content-type:text/plain\n\n";

    my @networks = ();
    foreach my $network (sort {lc($a->{network}) cmp lc($b->{network})} $uravo->getNetworks()) {
        push(@networks, $network->{network});
    }
    print encode_json(\@networks);
}
