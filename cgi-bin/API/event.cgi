#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use warnings;
use DBI;
use JSON;
use CGI;
use Data::Dumper;

my $dbh;
my $uravo;

eval {
    main();
};
print "Content-type: text/html\n\n$@" if ($@);

sub main {
    $uravo = new Uravo;
    my $query = new CGI;
    my $params = $query->Vars;
    $params->{'filter'} ||= 'Default';

    print "Content-type:text/plain\n\n";

    my $data = events($params);
    if (scalar(@$data) == 0 and $params->{'filter'} eq 'Default') {
        $params->{'filter'} = 'Default2';
        $data = events($params);
    }
    print encode_json($data);
    # Disconnect from the database
}

sub events {
    my $params = shift || return;

    my $filters = $uravo->{db}->selectall_hashref("SELECT * FROM filter", "id");
    $filters->{'all'}{'where_str'} = "Serial > 0";
    $filters->{'default'}{'where_str'} = "SuppressEscl < 4 and Severity >= " . ($uravo->{settings}->{minimum_severity}) . " and EventLevel >= 10 and ParentIdentifier IS NULL";

    my $filter = lc($params->{'filter'}) || 'default';
    my $Identifier = $params->{'Identifier'};
    my $ParentIdentifier = $params->{'ParentIdentifier'};
    my $Serial = $params->{'Serial'};
    my $server_id = $params->{'server_id'};

    # Define the SQL statement to be executed
    my $field_list = "Class, Identifier, UNIX_TIMESTAMP(LastOccurrence) as LastOccurrence, Tally, Depth, Serial, server_id, cluster_id, type_id, AlertGroup, Severity, Summary, Ticket, Note, Acknowledged, UNIX_TIMESTAMP(FirstOccurrence) as FirstOccurrence, AdditionalInfo, AlertKey, SiteList, UNIX_TIMESTAMP(StateChange) as StateChange, EventLevel, Action, rack_id, SuppressEscl, ParentIdentifier, Agent, cage_id, silo_id, Timeout";
    my $where = "SuppressEscl < 4 and Severity >= " . ($uravo->{settings}->{minimum_severity}) . " and EventLevel >= 10 and ParentIdentifier IS NULL";

    if ($Serial) {
        $where = "Serial=$Serial";
    } elsif ($Identifier) {
        $where = "Identifier='$Identifier'";
    } elsif ($ParentIdentifier) {
        $where = "ParentIdentifier='$ParentIdentifier'";
    } elsif ($server_id) {
        $where = "server_id='$server_id'";
    } elsif (defined($filters->{$filter})) {
        $where = $filters->{$filter}{where_str};
    }

    my $sql = qq(select $field_list from alert a where $where);

    # Prepare it
    my $sth = $uravo->{db}->prepare($sql);

    # Execute it
    $sth->execute;

    my @data = ();
    # Check for errors
    if ( $sth->errstr ) {
        print $sth->errstr, "\n";
    } else {
        # Process the output
        my $data = ();
        while ( my $data = $sth->fetchrow_hashref) {
            push(@data, $data);
        }
    }
    return \@data;
}

1;
