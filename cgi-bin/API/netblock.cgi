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

    if ($form->{netblock_id}) {
        my $netblock = $uravo->getNetblock($form->{netblock_id});
        if ($netblock) {
            print encode_json($netblock->data());
        }
    } else {
        my @netblocks = ();
        $form->{id_only} = 1;
        $form->{all_silos} = 1;

        foreach my $netblock (sort {lc($a) cmp lc($b)} $uravo->getNetblocks($form)) {
            push(@netblocks, $netblock);
        }
        print encode_json(\@netblocks);
    }

}
