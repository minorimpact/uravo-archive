#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $cluster_id   = $form->{"cluster_id"};

    if ($cluster_id) {
        my $changelog = {user=>$user, note=>"Deleted cluster '$cluster_id'."};
        Uravo::Serverroles::Cluster::delete({cluster_id=>$cluster_id},$changelog);
    }

    print "Location: clusters.cgi\n\n";
}
