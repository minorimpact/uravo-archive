#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval {
    main();
};
print "Content-type: text/html\n\n$@" if ($@);

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    print "Content-type: text/html\n\n";
    my $warning;
    my $filter_id = $form->{filter_id};
    my $new_filter = lc($form->{new_filter});
    my $new_where_str = $form->{new_where_str};
    $new_where_str =~s/"/'/g;


    if ($filter_id && $form->{delete}) {
        $uravo->{db}->do("DELETE FROM filter WHERE id=?", undef, ($filter_id));
    } elsif ($form->{save} && $new_filter && $new_where_str) {
        if ($new_filter eq 'all' || $new_filter eq 'default') {
            $warning = "'$new_filter' is reserved.";
        } else {
            eval {
                my $events = $uravo->{db}->selectrow_hashref("SELECT count(*) AS c FROM alert WHERE $new_where_str")->{c};
                $uravo->{db}->do("INSERT INTO filter (where_str, id, create_date) values (?, ?, NOW())", undef, ($new_where_str, $new_filter));
            };
            if ($@) {
                $warning = $@;
            }
        }
    }

    print <<HEAD;
<head>
    <title>Filters</title>
    <link rel=stylesheet type=text/css href=/uravo.css>
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
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
        <li><a href=rootcause.cgi>Root Cause</a></li>
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=networks.cgi>Networks</a></li>
    </ul>
</div>
<div id=content>
    <div class=warning>$warning</div>
<form method=POST>
<table cellspacing=0 border=0>
DATA

    my $count = 1;
    my $filters = $uravo->{db}->selectall_arrayref("SELECT * FROM filter ORDER BY id", {Slice=>{}});
    foreach my $filter (@$filters) {
        print "<tr>\n";
        print "<td>$filter->{id}</td>\n";
        print "<td>$filter->{where_str}</td>\n";
        print "<td>";
        print " <a href='filters.cgi?filter_id=$filter->{id}&delete=1'>X</a></td></tr>";
        $count++;
    }
    print <<DATA;
    <tr><td>New filter:<input type=text name=new_filter maxlength=25 value="$new_filter"></td><td><input type=text name=new_where_str maxlength=255 value="$new_where_str"></td><td><button name=save value=1>Add</button></td></tr>
</table>
</form>
</div>
DATA
}

