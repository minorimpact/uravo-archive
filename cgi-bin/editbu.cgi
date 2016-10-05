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

    my $bu_id          = $form->{bu_id};
    my $save		        = $form->{save};

    my $bu = $uravo->getBU($bu_id);
    if (!$bu) {
        print "Location: bus.cgi\n\n";
        exit;
    }

    if ($save) {
        my $changelog = {user=>$user,ticket=>$form->{ticket},note=>$form->{note}};
        $bu->update({contact=>$form->{contact}, comments=>$form->{comments}}, $changelog);

        print "Location: bu.cgi?bu_id=${\ $bu->id(); }\n\n";
        exit;
    }

    opendir(DIR, "/admin/code");
    my @versionList		= grep { !/^\./ } readdir(DIR);
    closedir(DIR);


    print "Content-type: text/html\n\n";
    print <<HEAD;
    <link rel="stylesheet" href="/uravo.css" />
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
<script>
\$(function () {
    \$( "#save-dialog" ).dialog({
      autoOpen: false,
      height: 350,
      width: 375,
      modal: true,
      buttons: {
        "Save Changes": function() {
            \$("#note").val(\$( "#save-dialog-note").val());
            \$("#ticket").val(\$( "#save-dialog-ticket").val());
            \$( this ).dialog( "close" );
            \$( "#editbu").submit();
        },
        Cancel: function() {
          \$( this ).dialog( "close" );
        }
      }
    });
 
    \$( "#save-changes").button().click(function(e) {
        e.preventDefault();
        \$("#save-dialog").dialog("open");
    });
    \$( "#delete-bu").button().click(function(e) {
        e.preventDefault();
        if(confirm('Are you sure you want to delete $bu_id?')) { 
            self.location='deletebu.cgi?bu_id=$bu_id';
        }
    });
});
</script>
HEAD
    print $uravo->menu();
print <<FORM;
<div id=links>
    <ul>
        <li><a href='bus.cgi'>All Business Units</a></li>
    </ul>
</div>
<div id=content>
    <h1>$bu_id</h1>
    <form method='POST' action='editbu.cgi' id='editbu'>
        <input type='hidden' name='bu_id' value='$bu_id'>
        <input type="hidden" id="ticket" name="ticket">
        <input type="hidden" id="save" name="save" value="1">
        <input type="hidden" id="note" name="note">
        <fieldset>
            <p>
                <label for=contact>
                    Contact Name
                    <span class=fielddesc>Primary contact for this Business Unit.</span>
                </label>
                <input type=text maxlength=50  name=contact value="${\ $bu->get('contact'); }" id=contact>
            </p>

            <p>
                <label for=comments>
                    Comments
                    <span class=fielddesc></span>
                </label>
                <textarea name=comments cols=50 rows=7>${\ $bu->get('comments'); }</textarea> 
            </p>

            <p>
                <button id="save-changes">Save Changes</button>
                <button id="delete-bu">Delete this BU</button>
            </p>
        </fieldset>
    </form>
</div>

<div id="save-dialog" title="Save Changes">
    <form>
        <fieldset>
            <lable for="save-dialog-ticket">Ticket</label>
            <input type="text" name="save-dialog-ticket" id="save-dialog-ticket" value="" class="text ui-widget-content ui-corner-all" />
            <lable for="save-dialog-note">Note</label>
            <input name="save-dialog-note" id="save-dialog-note" value="" class="text ui-widget-content ui-corner-all" maxlength=50/>
        </fieldset>
    </form>
</div>

FORM
}


