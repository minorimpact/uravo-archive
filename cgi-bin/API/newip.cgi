#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Netblock;
use JSON;
use CGI;

&main(); 

sub main {
    my $uravo = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print "Content-type:text/plain\n\n";

    my $netblock = new Uravo::Serverroles::Netblock($form->{netblock_id});
    print encode_json([$netblock->newip()]);
}
