#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval {
    main();
};
print "Content-type: text/html\n\n$@\n" if ($@);

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

   if ($form->{new_network}) {
        my $new_order = $uravo->{db}->selectrow_hashref("SELECT MAX(`network_order`)+1 as new_order FROM network")->{new_order};
        $uravo->{db}->do("INSERT INTO network(`network`, `network_order`, `default_interface_name`, `create_date`) VALUES (?, ?, ?, NOW())", undef, ($form->{new_network}, $new_order, $form->{new_default_interface_name}));
    } elsif ($form->{delete}) {
        my $network_count = $uravo->{db}->selectrow_hashref("SELECT COUNT(*) AS total FROM interface WHERE network=?", undef, ($form->{delete}));
        if ($network_count->{total} == 0) {
            $uravo->{db}->do("DELETE FROM network WHERE network=?", undef, ($form->{delete}));
        }
    }

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Networks</title>
    <link rel=stylesheet type=text/css href=/uravo.css>
</head>
HEAD
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href=settings.cgi>Settings</a></li>
        <li><a href=thresholds.cgi>Thresholds</a></li>
        <li><a href=escalations.cgi>Escalations</a></li>
        <li><a href=contacts.cgi>Contacts</a></li>
        <li><a href=processes.cgi>Processes</a></li>
        <li><a href=rootcause.cgi>Root Causes</a></li>
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=filters.cgi>Filters</a></li>
    </ul>
</div>
<div id=content>
<table cellspacing=0>
DATA

    my $count = 1;
    my $networks = $uravo->{db}->selectall_arrayref("SELECT n.*, COUNT(i.network) AS total FROM network n LEFT JOIN(interface i) ON n.network=i.network GROUP BY n.network ORDER BY n.network_order", {Slice=>{}});
    print "<tr><th></th><th>name</th><th>default interface name</th><th>interface count</th><th><b>delete</b></th></tr>\n";
    foreach my $network (@$networks) {
        print "<tr ${\ (($count % 2)?'':'bgcolor=lightblue') }>";
        print "<td align='right' valign='top'>${\ $count; }</td><td valign='top'>$network->{network}</td><td>$network->{default_interface_name}</td><td valign='top'>";
        print $network->{total};
        print "</td>";
        print "<td>";
        if ($network->{total} == 0) {
            print "&nbsp;<a href='networks.cgi?delete=$network->{network}'><img src=/images/trash_16.gif border=0></a>";
        }
        print "</td>";
        print "</tr>\n";
        $count++;
    }
    print "<form method=POST>\n";
    print "<tr ${\ (($count % 2)?'':'bgcolor=lightblue') }>\n";
    print "<td></td><td><input type=text maxlength='20' name='new_network'></td><td><input type=text maxlength='10' name='new_default_interface_name'></td><td><input type=submit value='Add Network'></td><td></td></tr>\n";
    print "</form>\n";

    print <<DATA;
</table>
</div>
DATA
}

