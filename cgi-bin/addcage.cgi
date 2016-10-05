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

    my $cage_id		= $form->{cage_id};
    my $error		= "";

    if ($cage_id) {
        my $changelog = {user=>$user, note=>"New cage:$cage_id"};

        my $old_sub		= $cage_id;
        if ($cage_id	=~/[A-Z]/) {
            $cage_id    = lc($cage_id);
            $error		.= "'$old_sub' is invalid: contains uppercase characters<br>\n";
            $error		.= "... changed to '$cage_id'.<br>\n" if ($cage_id);
        }
        $old_sub		= $cage_id;
        if ($cage_id	=~s/[^a-z0-9]//g) {
            $error		.= "'$old_sub' is invalid: contains invalid characters<br>\n";
            $error		.= "... changed to '$cage_id'.<br>\n" if ($cage_id);
        }
        if ($uravo->getCage($cage_id)) {
            $error		.= "'<a href='cage.cgi?cage_id=$cage_id'>$cage_id</a>' already exists.<br>\n";
            $cage_id	= "";
        }

        unless ($error)	{
            Uravo::Serverroles::Cage::add({cage_id=>$cage_id}, $changelog);
            print "Location: editcage.cgi?cage_id=$cage_id\n\n";
            exit;
        }
    }

    print "Content-type: text/html\n\n";
    print $uravo->menu();
print <<FORM;
<br>
<br>
<b>$error</b><br>
<form method=POST>
New cage id: <input type=text name=cage_id value='$cage_id'><br>
<input type=submit value="Add Type">
</form>

FORM
}
