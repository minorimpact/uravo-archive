#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use JSON;
use CGI;
use Data::Dumper;


main();

sub main {
    my $uravo  = new Uravo({loglevel=>0});
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    

    print "Content-type:text/plain\n\n";

    if ($ENV{REQUEST_METHOD} eq 'POST') {
        my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";
        my @keys = $query->param;
        foreach my $key (@keys) {
            $form->{$key} = $query->param($key);
        }
        $form->{'changelog'} = { user=>$user, note=>'API insert:' . $form->{server_id} };
        my $server = Uravo::Serverroles::Server::add($form);
        if ($server) {
            print encode_json($server->data());
        }
    } else {
        if ($form->{server_id}) {
            my $server = $uravo->getServer($form->{server_id});
            if ($server) {
                print encode_json($server->data());
            }
        } elsif ($form->{search}) {
            my $server = $uravo->getServer($form->{search},{all_silos=>1});
            if ($server) {
                print encode_json($server->data());
            } else {
                print encode_json([]);
            }
        } else {
            my @servers = ();
            $form->{id_only} = 1;
            $form->{all_silos} = 1;
            $form->{pre_sort} = 1;
            foreach my $server ($uravo->getServers($form)) {
                push(@servers, $server);
            }
            print encode_json(\@servers);
        }
    }
}
