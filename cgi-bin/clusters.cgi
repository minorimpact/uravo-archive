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

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Clusters</title>
    <link rel="stylesheet" type="text/css" href="/uravo.css">
</head>
HEAD
    print $uravo->menu();

    print <<DATA;
<div id=links>
    <ul>
       <li><a href="addcluster.cgi">Add new Cluster</a></li>
    </ul>
</div>
<div id="content">
    <ol>
DATA
    foreach my $cluster_id ( sort { uc($a) cmp uc($b) } $uravo->getClusters({id_only=>1})) {
        print "<li><a href=cluster.cgi?cluster_id=$cluster_id>$cluster_id</a></li>\n";
    }
    print <<DATA;
    </ol>
</div>
DATA
}

