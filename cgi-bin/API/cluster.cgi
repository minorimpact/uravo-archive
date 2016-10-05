#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use JSON;
use CGI;

&main(); 

sub main {
    my $uravo = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print "Content-type:text/plain\n\n";

    if ($form->{cluster_id}) {
        my $cluster = $uravo->getCluster($form->{cluster_id});
        if ($cluster) {
            print encode_json($cluster->data());
        }
    } else {
        my @clusters = ();
        my $silo;
        my $all_silos = 1;
        if ($form->{silo} || $form->{silo_id}) {
            $silo = $form->{silo} || $form->{silo_id};
            $all_silos = 0;
        }
        foreach my $cluster (sort {lc($a) cmp lc($b)} $uravo->getClusters({id_only=>1,all_silos=>$all_silos,silo=>$silo,type_id=>$form->{type_id}})) {
            push(@clusters, $cluster);
        }
        print encode_json(\@clusters);
    }

}
