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

    my $cage_id = $form->{"cage_id"};

    my $cage = new $uravo->getCage($cage_id);

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Cage: $cage_id</title>
    <link rel=stylesheet type=text/css href=/uravo.css>
</head>
HEAD
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href=cages.cgi>All Cages</a></li>
    </ul>
</div>
<div id=content>
    <h1>$cage_id ${\ $cage->link("config"); }</h1>
    <div class=field>
        <span class=label>Prefix</span>
        <span class=data>${\ $cage->get('prefix'); }</span>
    </div>

    <h2>Racks in this cage:</h2>
    <ol>
DATA
    foreach my $rack_id (sort { lc($a) cmp lc($b); } $cage->getRacks({id_only=>1})) {
        print "<li><a href=rack.cgi?rack_id=$rack_id>$rack_id</a></li>\n";
    }
    print <<DATA;
    </ol>
</div>
DATA

}

