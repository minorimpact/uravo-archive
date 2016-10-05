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

    if ($form->{type_id}) {
        my $type = $uravo->getType($form->{type_id});
        if ($type) {
            print encode_json($type->data());
        }
    } else {
        my @types = ();
        my $silo;
        my $all_silos = 1;
        if ($form->{silo} || $form->{silo_id}) {
            $silo = $form->{silo} || $form->{silo_id};
            $all_silos = 0;
        }

        foreach my $type (sort {lc($a) cmp lc($b)} $uravo->getTypes({id_only=>1,all_silos=>$all_silos,silo=>$silo,cluster_id=>$form->{cluster_id}})) {
            push(@types, $type);
        }
        print encode_json(\@types);
    }

}
