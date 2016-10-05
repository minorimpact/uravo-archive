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

    my $type_id		= $form->{type_id};
    my $error		= "";

    if ($type_id) {

        my $old_sub		= $type_id;
        if ($type_id	=~/[A-Z]/) {
            $type_id    = lc($type_id);
            $error		.= "'$old_sub' is invalid: contains uppercase characters<br>\n";
            $error		.= "... changed to '$type_id'.<br>\n" if ($type_id);
        }
        $old_sub		= $type_id;
        if ($type_id	=~s/[^a-z0-9]//g) {
            $error		.= "'$old_sub' is invalid: contains invalid characters<br>\n";
            $error		.= "... changed to '$type_id'.<br>\n" if ($type_id);
        }
        if ($uravo->getType($type_id)) {
            $error		.= "'<a href='type.cgi?type_id=$type_id'>$type_id</a>' already exists.<br>\n";
            $type_id	= "";
        }

        unless ($error)	{
        my $changelog = {user=>$user, note=>'New type.'};
            Uravo::Serverroles::Type::add({type_id=>$type_id}, $changelog);
            print "Location: edittype.cgi?type_id=$type_id\n\n";
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
New type id: <input type=text name=type_id value='$type_id'><br>
<input type=submit value="Add Type">
</form>

FORM
}
