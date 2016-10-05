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

    my @cages = new $uravo->getCages({id_only=>1});

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Cages</title>
    <link rel=stylesheet type=text/css href=/uravo.css>
</head>
HEAD
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href='addcage.cgi'>Add a Cage</a></li>
    </ol>
</div>
<div id=content>
    <ol>
DATA
    foreach my $cage_id (sort $uravo->getCages({id_only=>1})) {
        print "<li><a href='cage.cgi?cage_id=" . $cage_id . "'>" . $cage_id . "</a></li>\n";
    }
    print <<DATA;
    </ol>
</div>
DATA

}

