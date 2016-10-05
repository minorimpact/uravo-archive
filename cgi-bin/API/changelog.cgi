#!/usr/bin/perl


use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use JSON;
use CGI;

main();

sub main() {
	my $uravo = new Uravo;

	my $query = CGI->new();
	my %vars = $query->Vars;
	my $form = \%vars;

    print "Content-type: text/plain\n\n";

    my $object = $uravo->getObject("$form->{object_type},$form->{object_id}");

    my @changelogs = ();
    foreach my $changelog ($object->changelog()) {
        push(@changelogs, $changelog);
    }
    print encode_json(\@changelogs);
}

