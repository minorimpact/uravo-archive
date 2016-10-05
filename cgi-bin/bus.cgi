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
print qq(
<head>
    <title>Business Units</title>
    <link rel="stylesheet" type="text/css" href="/uravo.css">
</head>);

    print $uravo->menu();
    print qq(
<div id=links>
    <ul>
        <li><a href="addbu.cgi">Add new Business Unit</a></li>
    </ul>
</div>
<div id=content>
    <h1>Business Units</h1>
    <ol>);
    foreach my $bu_id ( sort { lc($a) cmp uc($b) } $uravo->getBUs({id_only=>1})) {
        print "<li><a href=bu.cgi?bu_id=$bu_id>$bu_id</a></li>\n";
    }
    print <<DATA;
    </ol>
</div>
DATA
}

