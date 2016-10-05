#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use JSON;
use CGI;

&main(); 

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;


    print "Content-type:text/plain\n\n";

    if ($form->{silo_id}) {
        my $silo = $uravo->getSilo($form->{silo_id});
        if ($silo) {
            print encode_json($silo->data());
        }
    } else {
        my @silos = ();
        foreach my $silo (sort {lc($a) cmp lc($b)} $uravo->getSilos({id_only=>1,bu=>$form->{bu_id}})) {
            push(@silos, $silo);
        }
        print encode_json(\@silos);
    }

}
