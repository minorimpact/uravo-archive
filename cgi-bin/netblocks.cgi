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

    print qq(Content-type: text/html

    <head>
        <title>Netblocks</title>
        <link rel="stylesheet" href="/uravo.css" />
    </head>);
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href="addnetblock.cgi">Add new Netblock</a></li>
    </ul>
</div>
<div id=content>
<h1>Netblocks</h1>
<ol>
DATA
    my @netblocks = $uravo->getNetblocks({id_only=>1});
    foreach my $netblock_id (sort {$a cmp $b } $uravo->getNetblocks({id_only=>1})) {
        print "<li><a href='netblock.cgi?netblock_id=$netblock_id'>$netblock_id</a></li>\n";
    }
    print <<DATA;
</ol>
</div>
DATA

}

