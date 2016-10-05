#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::BU;
use CGI;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $bu_id	= $form->{bu_id};

    if ($bu_id && $bu_id ne 'core') {
        my $changelog = {user=>$user,note=>"Business Unit deleted:$bu_id"};
        Uravo::Serverroles::BU::delete({bu_id=>$bu_id},$changelog);
    }
    
    print "Location: bus.cgi\n\n";
}

