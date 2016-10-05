#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use warnings;
use DBI;
use JSON;
use CGI;

my $dbh;
my $uravo;

main();

sub main {
    $uravo = new Uravo;
    my $query = new CGI;
    my $params = $query->Vars;

    my $Serial = $params->{'Serial'};

    print "Content-type:text/plain\n\n";

    my $dbh = $uravo->{db};
    my $results = $dbh->selectall_arrayref("select user_id, entry, create_date from alert_journal where Serial=? order by create_date asc", {Slice=>{}}, ($Serial));

    print encode_json($results);
}

1;
