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

    print "Content-type: text/html\n\n";
    print $uravo->menu();

    print <<DATA;
<head>
    <link rel="stylesheet" type="text/css" href="/uravo.css">
    <title>Types</title>
</head>

<div id=links>
    <ul>
        <li><a href="addtype.cgi">Add new Type</a></li>
    </ul>
</div>
<div id=content>
<h1>Types</h1>
<ol>
DATA
    my $count = 1;
    foreach my $type_id ( sort { lc($a) cmp lc($b); } $uravo->getTypes({id_only=>1})) {
        print "<li><a href=type.cgi?type_id=$type_id>$type_id</a></li>\n";
    }
    print <<DATA;
</ol>
</div>
DATA
}

