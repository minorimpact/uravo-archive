#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Rack;
use CGI;

&main;
exit;

sub main {
    my $query = new CGI;
    my $rack_id	= $query->param("rack_id");
    
    Uravo::Serverroles::Rack::delete($rack_id);

    print "Location: racks.cgi\n\n";
}

