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
    my $rack_id	= $form->{"rack_id"};
    my $cage_id	= $form->{"cage_id"};

    if ($rack_id) {
        my $original_rack_id	= $rack_id;
        if ($rack_id =~s/\W//g) {
            $warning	.= "'$original_rack_id' is invalid- changed to '$rack_id'.<br>\n";
        }

        unless ($rack_id) {
            $warning	.= "'$rack_id' is invalid.<br>\n";
        }

        if ($rack_id && $uravo->getRack($rack_id)) {
            $warning	.= "'<a href=rack.cgi?rack_id=$rack_id>$rack_id</a>' already exists.<br>\n";
        }

        unless ($warning) {
            my $changelog = {note=>'New rack.', user=>$user};
            my $rack = Uravo::Serverroles::Rack::add({rack_id=>$rack_id, cage_id=>$cage_id}, $changelog);
            if ($rack) {
                print "Location: editrack.cgi?rack_id=" . $rack->id() . "\n\n";
                exit;
            } else {
                $warning = "Unable to add rack.\n";
            }
        }
    }

    print "Content-type: text/html\n\n";
    my $cageOptionList = '';
    foreach my $cage_id ($uravo->getCages({id_only=>1})) {
        $cageOptionList .= "<option value='$cage_id'>$cage_id</option>\n";
    }

    print $uravo->menu();

    print <<FORM;
<form method=post>
</br>
<b>$warning</b></br>
<table>
    <tr>
        <td>Cage</td>
        <td><select name='cage_id'>$cageOptionList</select></td>
    </tr>
    <tr>
        <td>Rack No.</td>
        <td><input type='text' name='rack_id' value='$rack_id' maxlength=20></td>
    </tr>
    <tr>
        <td></td>
        <td><input type=submit value="Add Rack"></td>
    </tr>
</table>
</form>
FORM
}

