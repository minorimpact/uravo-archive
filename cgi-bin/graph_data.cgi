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

    my $server_id = $form->{server_id};
    my $graph_id = $form->{graph_id};
    my $range = $form->{range} || "e-48h";
    my $server = $uravo->getServer($server_id);
    print "Content-type: text/html\n\n";

    if ($server && $graph_id) {
        my $graph_data = $server->graph_data($graph_id, $range, 1);
        foreach my $time (sort keys %{$graph_data}) {
            foreach my $sub_id (sort keys %{$graph_data->{$time}}) {
                print "$time|$sub_id|" . $graph_data->{$time}{$sub_id}. "\n";
            }
        }
    }
}

