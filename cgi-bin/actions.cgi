#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval {
    main();
};
print "Content-type: text/html\n\n$@" if ($@);

sub moveUp {
    my $uravo = shift || return;
    my $action_id = shift || return;

    my $actionorder = $uravo->{db}->selectrow_hashref("SELECT actionorder FROM action WHERE id=?", undef, ($action_id))->{actionorder};
    if ($actionorder > 0) {
        my $next_actionorder = $uravo->{db}->selectrow_hashref("SELECT MAX(actionorder) as o FROM action WHERE actionorder<?", undef, ($actionorder))->{o};
        $uravo->{db}->do("UPDATE action SET actionorder=actionorder+1 WHERE actionorder=?", undef, ($next_actionorder));
        $uravo->{db}->do("UPDATE action SET actionorder=? WHERE id=?", undef, ($next_actionorder, $action_id));
    }
}

sub moveDown {
    my $uravo = shift || return;
    my $action_id = shift || return;

    my $actionorder = $uravo->{db}->selectrow_hashref("SELECT actionorder FROM action WHERE id=?", undef, ($action_id))->{actionorder};
    my $next_actionorder = $uravo->{db}->selectrow_hashref("SELECT MIN(actionorder) as o FROM action WHERE actionorder>?", undef, ($actionorder))->{o};
    $uravo->{db}->do("UPDATE action SET actionorder=actionorder-1 WHERE actionorder=?", undef, ($next_actionorder));
    $uravo->{db}->do("UPDATE action SET actionorder=? WHERE id=?", undef, ($next_actionorder, $action_id));
}

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    print "Content-type: text/html\n\n";
    my $action_id = $form->{action_id};
    my $symptom_id = $form->{symptom_id};
    if ($form->{move} && $action_id) {
        if ($form->{move} eq 'UP') {
            moveUp($uravo, $action_id);
        } elsif ($form->{move} eq 'DOWN') {
            moveDown($uravo, $action_id);
        }
    } elsif ($action_id && $form->{delete}) {
        $uravo->{db}->do("DELETE FROM action WHERE id=?", undef, ($action_id));
    } elsif ($form->{save} && $form->{new_action} && $form->{new_where_str}) {
        my $order = $uravo->{db}->selectrow_hashref("SELECT max(actionorder) as o FROM action")->{o};
        $uravo->{db}->do("INSERT INTO action (where_str, action, actionorder, create_date) values (?, ?,?, NOW())", undef, ($form->{new_where_str}, $form->{new_action}, $order+1));
        $action_id = $uravo->{db}->{mysql_insertid};
    }

    print <<HEAD;
<head>
    <title>Actions</title>
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
        <li><a href=networks.cgi>Networks</a></li>
        <li><a href=filters.cgi>Filters</a></li>
    </ul>
</div>
<div id=content>
<form method=POST>
<table cellspacing=0 border=0>
DATA

    my %actions = ( 'raise'=>'Increase Severity', 'lower'=>'Lower Severity', 'discard'=>'Discard', 'hide'=>'Hide' );

    my $count = 1;
    my $actions = $uravo->{db}->selectall_arrayref("SELECT * FROM action ORDER BY actionorder", {Slice=>{}});
    foreach my $action (@$actions) {
        print "<tr>\n";
        print "<td>$action->{where_str}</td>\n";
        print "<td>$actions{$action->{action}}</td>\n";
        print "<td>";
        print " <a href='actions.cgi?action_id=$action->{id}&move=DOWN'>DOWN</a>" if ($count < scalar(@$actions));
        print " <a href='actions.cgi?action_id=$action->{id}&move=UP'>UP</a>" if ($count > 1);
        print " <a href='actions.cgi?action_id=$action->{id}&delete=1'>X</a></td></tr>";
        $count++;
    }
    my $action_options = join('', map { "<option value=$_>$actions{$_}</option>"; } keys %actions);
    print <<DATA;
    <tr><td>New action:<input type=text name=new_where_str></td><td><select id=new_action name=new_action>$action_options</select></td><td><button name=save value=1>Add</button></td></tr>
</table>
</form>
</div>
DATA
}

