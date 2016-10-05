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
    my $rootcause_id = shift || return;

    my $causeorder = $uravo->{db}->selectrow_hashref("SELECT causeorder FROM rootcause WHERE id=?", undef, ($rootcause_id))->{causeorder};
    if ($causeorder > 0) {
        my $next_causeorder = $uravo->{db}->selectrow_hashref("SELECT MAX(causeorder) as o FROM rootcause WHERE causeorder<?", undef, ($causeorder))->{o};
        $uravo->{db}->do("UPDATE rootcause SET causeorder=causeorder+1 WHERE causeorder=?", undef, ($next_causeorder));
        $uravo->{db}->do("UPDATE rootcause SET causeorder=? WHERE id=?", undef, ($next_causeorder, $rootcause_id));
    }
}

sub moveDown {
    my $uravo = shift || return;
    my $rootcause_id = shift || return;

    my $causeorder = $uravo->{db}->selectrow_hashref("SELECT causeorder FROM rootcause WHERE id=?", undef, ($rootcause_id))->{causeorder};
    my $next_causeorder = $uravo->{db}->selectrow_hashref("SELECT MIN(causeorder) as o FROM rootcause WHERE causeorder>?", undef, ($causeorder))->{o};
    $uravo->{db}->do("UPDATE rootcause SET causeorder=causeorder-1 WHERE causeorder=?", undef, ($next_causeorder));
    $uravo->{db}->do("UPDATE rootcause SET causeorder=? WHERE id=?", undef, ($next_causeorder, $rootcause_id));
}

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    print "Content-type: text/html\n\n";
    my $rootcause_id = $form->{rootcause_id};
    my $symptom_id = $form->{symptom_id};
    if ($form->{move} && $rootcause_id) {
        my $causeorder = $uravo->{db}->selectrow_hashref("SELECT causeorder FROM rootcause WHERE id=?", undef, ($rootcause_id))->{causeorder};
        if ($form->{move} eq 'UP') {
            moveUp($uravo, $rootcause_id);
        } elsif ($form->{move} eq 'DOWN') {
            moveDown($uravo, $rootcause_id);
        }
    } elsif ($symptom_id && $form->{delete}) {
        $uravo->{db}->do("DELETE FROM rootcause_symptom WHERE id=?", undef, ($symptom_id));
    } elsif ($rootcause_id && $form->{delete}) {
        $uravo->{db}->do("DELETE FROM rootcause_symptom WHERE rootcause_id=?", undef, ($rootcause_id));
        $uravo->{db}->do("DELETE FROM rootcause WHERE id=?", undef, ($rootcause_id));
    } elsif ($form->{save} && $form->{new_rootcause} && $form->{new_symptom}) {
        my $order = $uravo->{db}->selectrow_hashref("SELECT max(causeorder) as o FROM rootcause")->{o};
        $uravo->{db}->do("INSERT INTO rootcause (where_str, causeorder, create_date) values (?, ?, NOW())", undef, ($form->{new_rootcause}, $order+1));
        $rootcause_id = $uravo->{db}->{mysql_insertid};
        foreach my $symptom (split(/\0/, $form->{new_symptom})) {
            $uravo->{db}->do("INSERT INTO rootcause_symptom (rootcause_id, where_str, create_date) values (?, ?, NOW())", undef, ($rootcause_id, $symptom));
        }
    } elsif ($rootcause_id && $form->{new_symptom2}) {
            $uravo->{db}->do("INSERT INTO rootcause_symptom (rootcause_id, where_str, create_date) values (?, ?, NOW())", undef, ($rootcause_id, $form->{new_symptom2}));
    }

    print <<HEAD;
<head>
    <title>Root Causes</title>
    <link rel=stylesheet type=text/css href=/uravo.css>
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>

    <script>
        \$(function () {
            \$( ".new_symptom_cell").on( {
                keyup: function() {
                    var blank = 0;
                    \$(this).closest("td").find("input").each(function() {
                        if (\$(this).val() == '') {
                            blank++;
                            if (blank > 1) {
                                \$(this).remove();
                                blank--;
                            }
                        }
                    });
                    if (!blank) {
                        \$(this).closest("td").append("<input type=text id=new_symptom name='new_symptom' value=''>");
                    }
                }
            }, 'input');
        });
    </script>
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
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=networks.cgi>Networks</a></li>
        <li><a href=filters.cgi>Filters</a></li>
    </ul>
</div>
<div id=content>
<form method=POST>
<table cellspacing=0 border=0>
DATA

    my $count = 1;
    my $causes = $uravo->{db}->selectall_arrayref("SELECT * FROM rootcause ORDER BY causeorder", {Slice=>{}});
    foreach my $cause (@$causes) {
        print "<tr>\n";
        print "<td colspan=2>$cause->{where_str}</td>\n";
        print "<td align=right><a href='rootcause.cgi'>" . ($rootcause_id == $cause->{id}?"<a href='rootcause.cgi'>-</a>":"<a href='rootcause.cgi?rootcause_id=$cause->{id}'>+</a>");
        print " <a href='rootcause.cgi?rootcause_id=$cause->{id}&move=DOWN'>DOWN</a>" if ($count < scalar(@$causes));
        print " <a href='rootcause.cgi?rootcause_id=$cause->{id}&move=UP'>UP</a>" if ($count > 1);
        print " <a href='rootcause.cgi?rootcause_id=$cause->{id}&delete=1'>X</a></td></tr>";
        if ($rootcause_id == $cause->{id}) {
            my $symptoms = $uravo->{db}->selectall_arrayref("SELECT * FROM rootcause_symptom WHERE rootcause_id=?", {Slice=>{}}, ($cause->{id}));
            foreach my $symptom (@$symptoms) {
                print "<tr><td>&nbsp; &nbsp;</td><td>$symptom->{where_str}</td><td><a href=rootcause.cgi?rootcause_id=$cause->{id}&symptom_id=$symptom->{id}&delete=1>X</a></td></tr>\n";
            }
            print "<tr><td>&nbsp; &nbsp;</td><td>New Symptom:<input type=text id=new_symptom name=new_symptom2></td><td><button name=rootcause_id value=$cause->{id}>Add</button></td></tr>\n";
        }
        $count++;
    }
    print <<DATA;
    <tr><td>New cause:<input type=text name=new_rootcause></td><td class=new_symptom_cell>New Symptoms:<input type=text id=new_symptom name=new_symptom></td><td><button name=save value=1>Add</button></td></tr>
</table>
</form>
</div>
DATA
}

