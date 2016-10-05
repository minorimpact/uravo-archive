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

    my $silo_id	= $form->{silo_id};

    if ($silo_id) {
        my $changelog = {user=>$user,note=>"Silo deleted:$silo_id"};
        Uravo::Serverroles::Silo::delete({silo_id=>$silo_id}, $changelog);
    }
    
    print "Location: silos.cgi\n\n";
}

