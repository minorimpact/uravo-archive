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

    my $cage_id	= $form->{cage_id};

    if ($cage_id && $cage_id ne 'core') {
        my $changelog = {user=>$user,note=>"Cage deleted:$cage_id"};
        Uravo::Serverroles::Cage::delete({cage_id=>$cage_id},$changelog);
    }
    
    print "Location: cages.cgi\n\n";
}

