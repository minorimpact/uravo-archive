#!/usr/bin/perl

use lib "/usr/local/uravo/lib";
use strict;
use Uravo;
use Uravo::Serverroles::Netblock;
use CGI;

eval {
    main();
};
print "Content-type:text/html\n\n$@" if ($@);

sub main {
    my $query = new CGI;
    my $netblock_id	= $query->param("netblock_id");
    
    Uravo::Serverroles::Netblock::delete($netblock_id);

    print "Location: netblocks.cgi\n\n";
}

