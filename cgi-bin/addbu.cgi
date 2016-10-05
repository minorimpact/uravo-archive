#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::BU;
use CGI;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $bu_id	= $form->{bu_id};
    my $warning	= "";

    if ($bu_id) {
        my $changelog = {user=>$user, note=>'New business unit.'};

        my $original_bu_id = $bu_id;
        if ($bu_id =~/[A-Z]/) {
            $bu_id = lc($bu_id);
            $warning .= "'$original_bu_id' contains uppercase letters, changed to '$bu_id'.";
        }

        if (length($bu_id) < 3) {
            $warning .= "'$bu_id' is too short. bu_id needs to be at least 3 characters.";
        }

        $original_bu_id = $bu_id;
        if ($bu_id =~s/\W//g) {
            $warning .= "'$original_bu_id' contains invalid characters, changed to '$bu_id'.";
        }

        unless ($bu_id) {
            $warning	.= "'$bu_id' is invalid.<br>\n";
        }

        if ($bu_id && $uravo->getBU($bu_id)) {
            $warning	.= "'<a href='bu.cgi?bu_id=$bu_id'>$bu_id</a>' already exists.";
        }

        unless ($warning) {
            Uravo::Serverroles::BU::add({bu_id=>$bu_id}, $changelog);
            print "Location: editbu.cgi?bu_id=$bu_id\n\n";
            exit;
        }
    }

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Add Business Unit</title>
    <link rel=stylesheet type=text/css href=/uravo.css>
</head>
HEAD
    print $uravo->menu();

print <<FORM;
<div id=links>
    <ul>
        <li><a href=bus.cgi>All Business Units</a></li>
    </ul>
</div>
<div id=content>
    <h1>Add a new New Business Unit</h1>
    <h2 class=warning>$warning</h2>
    <form method=post>
        <fieldset>
            <p>
                <label for=bu_id>
                    Business Unit ID
                    <span class=fielddesc>[a-z], [0-9], _ only, no special characters.</span>
                </label>
                <input type=text name=bu_id value="$bu_id" maxlength=20><br>
            </p>
            <p>
                <button name=save id=save>Add Business Unit</button>
            </p>
        </fieldset>
    </form>
</div>
FORM
}


