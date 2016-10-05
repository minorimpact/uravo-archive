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

    my $netblock_id = $form->{netblock_id} || die "No netblock id.\n";

    my $netblock = $uravo->getNetblock($netblock_id) || die "Can't create netblock object.\n";


    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Netblock: $netblock_id</title>
    <link rel=stylesheet type=text/css href=/uravo.css />
</head>
HEAD

    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href=netblocks.cgi>All Netblocks</a></li>
    </ul>
</div>
<div id=content>
    <h1>$netblock_id ${\ $netblock->link('default -info'); }</h1>
    <div class=field>
        <span class=label>Address</span>
        <span class=data> ${\ $netblock->get("address"); }</span>
    </div>
    <div class=field>
        <span class=label>Silo</span>
        <span class=data>${\ ($netblock->get("network")?"<a href='/cgi-bin/silo.cgi?silo_id=" . $netblock->get("silo_id") . "'>" . $netblock->get("silo_id") . "</a>":""); }</span>
    </div>
    <div class=field>
        <span class=label>Network</span>
        <span class=data> ${\ $netblock->get("network"); }</span>
    </div>
    <div class=field>
        <span class=label>Included in discovery</span>
        <span class=data>${\ ($netblock->get('discovery')?"Yes":"No");}</span>
    </div>
</div>
DATA
}

