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

    my $cage_id = $form->{cage_id};
    my $save = $form->{save};
    my $prefix = $form->{prefix};
    my $cage = $uravo->getCage($cage_id);
    if (!$cage) {
        print "Location: cagess.cgi\n\n";
        exit;
    }


    if ($cage_id && $save) {
        my $changelog = {note=>'', ticket=>'', user=>$user};
        $cage->update({prefix=>$prefix}, $changelog);
        print "Location: cage.cgi?cage_id=$cage_id\n\n";
        exit;
    }
    
    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Edit Cage: $cage_id</title>
    <link rel="stylesheet" type=text/css href="/uravo.css">
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
<script>
\$(function () {
    \$( "#delete-cage").button().click(function(e) {
            e.preventDefault();
            if(confirm('Are you sure you want to delete $cage_id?')) { 
                self.location='deletecage.cgi?cage_id=$cage_id';
            }
    });
});
</script>
<head>
HEAD
    print $uravo->menu();
     
    print <<FORM;
<div id=links>
    <a href=cages.cgi>All Cages</a>
</div>

<div id=content>
    <h1>$cage_id</h1>
    <form method='POST'>
        <input type="hidden" name="cage_id" value="$cage_id">
        <fieldset>
            <p>
                <label for=prefix>
                    Prefix
                    <span class=fielddesc>Append this string to the id of all racks in this cage.</span>
                </label>
                <input type=text value="${\ $cage->get('prefix'); }" id=prefix name=prefix>
            </p>

            <p>
                <button id="save-changes" name=save>Save Changes</button>
                <button id="delete-cage">Delete this Cage</button>
            </p>
        </fieldset>
    </form>
</div>
FORM

}

