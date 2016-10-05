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

    my $type_id   = $form->{type_id};

    if ($type_id) {
        my $changelog = {user=>$user, note=>"Deleted type '$type_id'."};
        Uravo::Serverroles::Type::delete({type_id=>$type_id}, $changelog);
    }

    print "Location: types.cgi\n\n";
}

