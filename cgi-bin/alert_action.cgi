#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use JSON;
use CGI;

my $uravo = new Uravo;
my $query = new CGI;
my $params = $query->Vars;

my $action = $params->{"action"};

my $Serial = $params->{'Serial'};
die "Invalid serial\n" if ($Serial =~/[^0-9,]/);
my @Serials = split(/,/, $Serial);

print "Content-type:text/html\n\n";
my $username = $ENV{'REMOTE_USER'} || die "INVALID USER";

my $dbh = $uravo->{db};

my %actions = ( ack=>\&ack,
                assignticket => \&assignticket,
                assigntorollup => \&assigntorollup,
                combine => \&combine,
                createticket => \&createticket,
                deleteevent => \&deleteevent,
                hide => \&hide,
                removeticket => \&removeticket,
                removenote => \&removenote,
                updatenote => \&updatenote
            );

eval {
    $actions{$action}->($params);
};
die ($@) if ($@);

sub ack {
    foreach my $serial (@Serials) {
        $dbh->do("update alert set Acknowledged=1 where Serial = $serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Alert acknowledged by $username."));
    }
}

sub assignticket {
    my $params = shift;

    my $Ticket = $params->{Ticket};

    foreach my $serial (@Serials) {
        $dbh->do("update alert set Acknowledged=1, Action=3, ActionData='$Ticket' where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Ticket $Ticket assigned by $username."));
    }
}

sub assigntorollup {
    my $params = shift;

    my $ParentIdentifier = $params->{ParentIdentifier};
    foreach my $serial (@Serials) {
        $dbh->do("update alert set ParentIdentifier='$ParentIdentifier' where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Event assigned to $ParentIdentifier by $username."));
    }
}

sub combine {
    my $params = shift || return;

    my $new_summary = $params->{'new_summary'};
    die "No Summary\n" unless ($new_summary);

    my $now = localtime(time);
    my $ParentIdentifier = "global rollup $username:$now  alert_action.cgi";

    $dbh->do("insert into alert (EventLevel,server_id, Identifier, Summary, Class, AlertGroup, Severity, FirstOccurrence, LastOccurrence, AlertKey, Agent, Acknowledged) values (10, 'global', '$ParentIdentifier' ,'$new_summary', 100000, 'rollup', 4, NOW(), NOW(),'$username:$now', 'alert_action.cgi', 1)");
    foreach my $serial (@Serials) {
        $dbh->do("update alert set Acknowledged=1, ParentIdentifier='$ParentIdentifier' where Serial = $serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Manually rolled into $ParentIdentifier by $username."));
    }
}

sub createticket {
    foreach my $serial (@Serials) {
        $dbh->do("update alert set Acknowledged=1, Action=1, ActionData='$username:" . time() . "' where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Ticket created by $username."));
    }
}

sub deleteevent {
    foreach my $serial (split(/,/, $Serial)) {
        my $data = $dbh->selectrow_hashref("select Identifier from alert where Serial=?", undef, ($serial));
        my $Identifier = $data->{Identifier} if ($data && defined($data->{Identifier}));
        next unless ($Identifier);

        $dbh->do("UPDATE alert SET ParentIdentifier=NULL where ParentIdentifier='$Identifier'");
        $dbh->do("update alert set Severity=0, DeletedBy = '$username' where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Alert cleared by $username."));
    }
}

sub hide {
    foreach my $serial (@Serials) {
        $dbh->do("update alert set SuppressEscl=5 where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Alert hidden by  $username."));
    }
}

sub removeticket {
    foreach my $serial (@Serials) {
        my $data = $dbh->selectrow_hashref("select Identifier from alert where Serial=?", undef, ($serial));
        my $Identifier = $data->{Identifier} if ($data && defined($data->{Identifier}));
        next unless ($Identifier);

        $dbh->do("delete from custom.ticketing where Identifier='$Identifier'");
        $dbh->do("update alert set Acknowledged=1, Ticket=NULL where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Ticket removed by $username."));
    }
}

sub removenote {
    foreach my $serial (@Serials) {
        my $data = $dbh->selectrow_hashref("select Identifier from alert where Serial=?", undef, ($serial));
        my $Identifier = $data->{Identifier} if ($data && defined($data->{Identifier}));
        next unless ($Identifier);

        $dbh->do("delete from custom.ticketing where Identifier='$Identifier'");
        $dbh->do("update alert set Acknowledged=1, Note='' where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Note removed by $username."));
    }
}

sub updatenote {
    my $params = shift;

    my $Note = $params->{Note};
    foreach my $serial (@Serials) {
        $dbh->do("update alert set Acknowledged=1, Note='$Note' where Serial=$serial");
        $dbh->do("INSERT INTO alert_journal (Serial, user_id, entry, create_date) VALUES (?, ?, ?, NOW())", undef, ($serial, $username, "Note updated by $username."));
    }
}

