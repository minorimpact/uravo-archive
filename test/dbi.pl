#!/usr/bin/perl


use strict;
use DBI;

#my $dsn = "DBI:mysql:database=uravo;host=db.minorimpact.com";
print "Creating dsn\n";
my $dsn = "DBI:mysql:database=uravo;host=10.128.47.76";
print "connecting to $dsn\n";
my $db = DBI->connect($dsn, "uravo", "uravo");
print "select count(*) from server\n";
print $db->selectrow_hashref("select count(*) as count from server")->{count} ."\n";
print "done\n";


