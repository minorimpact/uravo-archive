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

    my $warning	= "";
    my $netblock_id	= $form->{"netblock_id"};
    if ($netblock_id) {
        my $original_netblock_id	= $netblock_id;
        if ($netblock_id =~s/\W//g) {
            $warning	.= "'$original_netblock_id' is invalid- changed to '$netblock_id'.<br>\n";
        }

        unless ($netblock_id) {
            $warning	.= "'$netblock_id' is invalid.<br>\n";
        }

        if ($netblock_id && $uravo->getNetblock($netblock_id)) {
            $warning	.= "<a href='netblock.cgi?netblock_id=$netblock_id'>$netblock_id</a> already exists.<br>\n";
        }

        unless ($warning) {
            my $changelog = {note=>$0, user=>$user};
            Uravo::Serverroles::Netblock::add({netblock_id=>$netblock_id}, $changelog);
            print "Location: editnetblock.cgi?netblock_id=$netblock_id\n\n";
            exit;
        }
    }

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Add new netblock</title>
    <link rel=stylesheet href=/uravo.css>
</head>
HEAD
    print $uravo->menu();

    print <<FORM;
<div id=links>
    <ul>
        <li><a href=netblocks.cgi>All Netblocks</a></li>
    </ul>
</div>
<div id=content>
<h2 class=warning>$warning</h2>
<form method=post>
    <fieldset>
        <p>
            <label for=netblock_id>
                Netblock ID
                <span class=fielddesc></span>
            </label>
            <input type='text' name='netblock_id' value='$netblock_id' maxlength='20'>
        </p>
        <button>Add Netblock</button>
    </fieldset>
</form>
</div>
FORM
}

