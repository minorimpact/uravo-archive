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

    my $silo_id	= $form->{silo_id};
    my $bu_id = $form->{bu_id};
    my $warning	= "";

    if ($silo_id) {
        my $changelog = {user=>$user, note=>'New silo.'};

        unless ($bu_id) {
            $warning .= "You must specify a business unit.\n";
        }

        my $original_silo_id = $silo_id;
        if ($silo_id =~/[A-Z]/) {
            $silo_id = lc($silo_id);
            $warning .= "'$original_silo_id' is invalid: contains uppercase letters.<br />\n";
            $warning .= "... changed to '$silo_id'.<br>\n";
        }

        if (length($silo_id) < 3) {
            $warning .= "'$silo_id' is invalid: too short.  silo_id needs to be at least 3 characters.<br />\n";
        }

        $original_silo_id = $silo_id;
        if ($silo_id =~s/\W//g) {
            $warning .= "'$original_silo_id' is invalid: contains invalid characters.<br />\n";
            $warning .= "... changed to '$silo_id'.<br>\n";
        }

        unless ($silo_id) {
            $warning	.= "'$silo_id' is invalid.<br>\n";
        }

        if ($silo_id && $uravo->getSilo($silo_id)) {
            $warning	.= "'<a href='silo.cgi?silo_id=$silo_id'>$silo_id</a>' already exists.<br>\n";
        }

        unless ($warning) {
            Uravo::Serverroles::Silo::add({bu_id=>$bu_id,silo_id=>$silo_id}, $changelog);
            print "Location: editsilo.cgi?silo_id=$silo_id\n\n";
            exit;
        }
    }

    print "Content-type: text/html\n\n";
    my $buSelect = "<select name=bu_id>";
    foreach my $bu (sort {$a cmp $b} $uravo->getBUs({id_only=>1,all_silos=>1})) {
        $buSelect .= "<option value='$bu'" .(($bu eq $bu_id)?' selected':'') . ">$bu</option>\n";
    }
    $buSelect .= "</select>";
    print $uravo->menu();

print <<FORM;
<form method=post>
<br>
<b>$warning</b><br>
<br>
Enter new silo id: <input type=text name=silo_id value="$silo_id" maxlength=20><br />
Business Unit: $buSelect<br />
<input type=submit value="Add Silo"><br>
</form>
FORM
}


