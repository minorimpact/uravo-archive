#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Server;
use CGI;

eval {
    main();
};
print "Content-type: text/html\n\n$@" if ($@);

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $server_id	= $form->{server_id};

    if ($server_id) {
        my $changelog = {user=>$user,note=>"Server deleted."};
        Uravo::Serverroles::Server::delete({server_id=>$server_id,changelog=>$changelog});
    }
    
    print "Location: index.cgi\n\n";
}

