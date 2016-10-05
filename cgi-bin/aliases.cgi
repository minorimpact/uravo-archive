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

    my $aliases = $uravo->{db}->selectall_arrayref("SELECT * FROM interface_alias ORDER BY alias", {Slice=>{}});
 
    print "Content-type: text/html\n\n";
    print $uravo->menu();

    print "<table cellspacing=0 style='padding-left:5px;'><tr><td></td><td><b>Alias</b></td><td><b>Server</b></td><td><b>Network</b></td><td><b>IP</b></td><td><b>Interface Name</b></td></tr>\n";
    my $count = 1;
    foreach my $alias (@$aliases) {
        my $interface = new Uravo::Serverroles::Interface($alias->{interface_id});
        print "<tr ${\ (($count % 2)?'':'bgcolor=lightblue') }>\n";
        print "<td style='padding-left:5px;'>${\ $count; }.</td>\n";
        print "<td style='padding-left:5px;'>$alias->{alias}.</td>\n";
        print "<td style='padding-left:5px;'><a href=server.cgi?server_id=" . $interface->get('server_id') . ">" . $interface->get('server_id') . "</a></td>\n";
        print "<td style='padding-left:5px;'>" . $interface->get('network') . "</td>\n";
        print "<td style='padding-left:5px;'>" . $interface->get('ip') . "</td>\n";
        print "<td style='padding-left:5px;'>" . $interface->get('name') . "</td>\n";
        print "</tr>\n";
        $count++;
    }
    print "</table>\n";
}

