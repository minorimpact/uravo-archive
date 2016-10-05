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

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $contact_group  = $form->{contact_group};

    if ($contact_group) {
        #my $changelog = {user=>$user, note=>"Deleted contact group '$contact_group'."};
        $uravo->{db}->do("DELETE FROM contacts WHERE contact_group=?", undef, ($contact_group)) || die ($uravo->{db}->errstr);
    }

    print "Location: contacts.cgi\n\n";
}

