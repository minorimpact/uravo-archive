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

    my $rack_id = $form->{"rack_id"} || die "No rack_id.\n";
    my $rack = $uravo->getRack($rack_id) || die "Can't create Rack object.\n";
    
    my $netblockSelect;
    my $networkSelect;
    my $cage = $rack->getCage();
    my $cage_id = $cage->id();

    my $count = 1;
    my $serverList = "<ol>\n";
    foreach my $server_id ($uravo->getServers({rack=>$rack_id,pre_sort=>1, all_silos=>1, id_only=>1})) {
        $serverList     .= "<li><a href='server.cgi?server_id=$server_id'>$server_id</a></span></li>\n";
    }
    $serverList .= "</ol>\n";

    print "Content-type: text/html\n\n";
    print <<HEADER;
<head>
    <title>Rack: $rack_id</title>
    <link rel='stylesheet' href='/uravo.css' />
</head>
HEADER
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <a href='racks.cgi'>All Racks</a>
</div>
<div id=content>
    <h1>$rack_id ${\ $rack->link('default -info'); }</h1>
    <div class=field>
        <span class=label>Cage</span>
        <span class=data><a href='cage.cgi?cage_id=$cage_id'>$cage_id</a></span>
    </div>
    <div class=field>
        <span class=label>X Position</span>
        <span class=data>${\ $rack->get('x_pos'); }</span>
    </div>
    <div class=field>
        <span class=label>Y Position</span>
        <span class=data>${\ $rack->get('y_pos'); }</span>
    </div>
    <h2>Servers in this rack:</h2>
    $serverList
</div>
DATA
}
