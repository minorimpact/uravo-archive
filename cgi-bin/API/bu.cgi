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

    if ($form->{bu_id}) {
        my $bu = $uravo->getBU($form->{bu_id});
        if ($bu) {
            print encode_json($bu->data());
        }
    } else {
        my @bus = ();
        foreach my $bu (sort {lc($a) cmp lc($b)} $uravo->getBUs({id_only=>1})) {
            push(@bus, $bu);
        }
        print encode_json(\@bus);
    }

}
