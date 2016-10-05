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

   if ($form->{new_process}) {
        $uravo->{db}->do("INSERT INTO process (name, create_date) VALUES (?, NOW())", undef, ($form->{new_process}));
    } elsif ($form->{delete}) {
        my $type_process_count = $uravo->{db}->selectrow_hashref("SELECT COUNT(*) AS total FROM type_process WHERE process_id=?", undef, ($form->{delete}));
        if ($type_process_count->{total} == 0) {
            $uravo->{db}->do("DELETE FROM process WHERE process_id=?", undef, ($form->{delete}));
        }
    }

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Contact Groups</title>
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
        <li><a href=rootcause.cgi>Root Causes</a></li>
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=filters.cgi>Filters</a></li>
    </ul>
</div>
<div id=content>
<table cellspacing=0>
DATA

    my $count = 1;
    my $processes = $uravo->{db}->selectall_arrayref("SELECT p.*, COUNT(tp.process_id) AS total FROM process p LEFT JOIN(type_process tp) ON tp.process_id=p.process_id GROUP BY p.process_id ORDER BY p.name", {Slice=>{}});
    print "<tr><td></td><td>&nbsp;</td><td><b>name</b></td><td>&nbsp;</td><td><b>type count</b></td><td>&nbsp;</td><td><b>delete</b></td></tr>\n";
    foreach my $process (@$processes) {
        print "<tr ${\ (($count % 2)?'':'bgcolor=lightblue') }>";
        print "<td align='right' valign='top'>${\ $count; }</td><td>&nbsp;</td><td valign='top'>$process->{name}</td><td>&nbsp;</td><td valign='top'>";
        if ($form->{show_types} == $process->{process_id}) {
            my $type_processes = $uravo->{db}->selectall_arrayref("SELECT * FROM type_process WHERE process_id=?", {Slice=>{}}, ($process->{process_id}));
            foreach my $type_process (@$type_processes) {
                print "<a href=type.cgi?type_id=$type_process->{type_id}>$type_process->{type_id}</a> ";
            }
        } else {
            if ($process->{total} == 0) {
                print "0";
            } else {
                print "<a href='processes.cgi?show_types=$process->{process_id}'>" . $process->{total} . "</a>";
            }
        }
        print "</td><td>&nbsp;</td>";
        print "<td>";
        if ($process->{total} == 0) {
            print "&nbsp;<a href='processes.cgi?delete=$process->{process_id}'><img src=/images/trash_16.gif border=0></a>";
        }
        print "</td>";
        print "</tr>\n";
        $count++;
    }
    print "<form method=POST>\n";
    print "<tr ${\ (($count % 2)?'':'bgcolor=lightblue') }>\n";
    print "<td></td><td>&nbsp;</td><td><input type=text maxlength='32' name='new_process'></td><td>&nbsp;</td><td colspan=3><input type=submit value='Add Process'></td>\n";
    print "</tr>\n";
    print "</form>\n";

    print <<DATA;
</table>
</div>
DATA
}

