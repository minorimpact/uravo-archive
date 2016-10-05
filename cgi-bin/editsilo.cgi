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

    my $silo_id = $form->{silo_id};
    my $save = $form->{save};

    my $silo = $uravo->getSilo($silo_id);
    if (!$silo) {
        print "Location: silos.cgi\n\n";
        exit;
    }
    my $bu = $silo->getBU();

    if ($save) {
        my $changelog = {user=>$user,ticket=>$form->{ticket},note=>$form->{note}};
        $silo->update({bu_id=>$form->{bu_id},comments=>$form->{comments}}, $changelog);

        print "Location: silo.cgi?silo_id=${\ $silo->id(); }\n\n";
        exit;
    }

    print "Content-type: text/html\n\n";
    my $buSelect = "<select name=bu_id>";
    foreach my $bu_id (sort $uravo->getBUs({id_only=>1,all_silos=>1})) {
        $buSelect .= "<option value='$bu_id'" .(($bu_id eq $bu->id())?' selected':'') . ">$bu_id</option>\n";
    }
    $buSelect .= "</select>";

    print <<HEAD;
<head>
    <link rel="stylesheet" href="/uravo.css">
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <style>
        label, input, textarea { display:block; }
        input.text, input.textarea { margin-bottom:12px; width:95%; padding: .4em; }
        fieldset { padding:0; border:0; margin-top:25px; }
    </style>
<script>
\$(function () {
    \$( "#save-dialog" ).dialog({
      autoOpen: false,
      height: 350,
      width: 375,
      modal: true,
      buttons: {
        Cancel: function() {
          \$( this ).dialog( "close" );
        },
        "Save Changes": function() {
            \$("#note").val(\$( "#save-dialog-note").val());
            \$("#ticket").val(\$( "#save-dialog-ticket").val());
            \$( this ).dialog( "close" );
            \$( "#editsilo").submit();
        }
      }
    });
 
    \$( "#save-changes").button().click(function() {
        \$("#save-dialog").dialog("open");
    });
    \$( "#delete-silo").button().click(function(e) {
        e.preventDefault();
        if(confirm('Are you sure you want to delete $silo_id?')) { 
            self.location='deletesilo.cgi?silo_id=$silo_id';
        }
    });
});
</script>
</head>
HEAD
    print $uravo->menu();
    print <<FORM;
<div id=links>
</div>
<div id=content>
<h1>${\ $silo->id(); }</h1>
<form method='POST' action='editsilo.cgi' id='editsilo'>
<input type='hidden' name='silo_id' value='$silo_id'>
<input type="hidden" id="ticket" name="ticket">
<input type="hidden" id="save" name="save" value="1">
<input type="hidden" id="note" name="note">
    <fieldset>
        <p>
            <label for=bu>
                Business Unit
                <span class="fielddesc"></span>
            </label>
            $buSelect
        </p>
        <p>
            <label for=comments>
                Comments
                <span class="fielddesc"></span>
            </label>
            <textarea name=comments cols=50 rows=7>${\ $silo->get('comments'); }</textarea> 
        </p>
        <p>
                <button id="save-changes">Save Changes</button>
                <button id="delete-silo">Delete this Silo</button>
        </p>
    </fieldset>
</form>
</div>

<div id="save-dialog" title="Save Changes">
    <form>
        <fieldset>
            <lable for="save-dialog-ticket">Jira Ticket</label>
            <input type="text" name="save-dialog-ticket" id="save-dialog-ticket" value="" class="text ui-widget-content ui-corner-all" />
            <lable for="save-dialog-note">Note</label>
            <input name="save-dialog-note" id="save-dialog-note" value="" class="text ui-widget-content ui-corner-all" maxlength=50/>
        </fieldset>
    </form>
</div>

FORM
}


