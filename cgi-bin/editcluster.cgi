#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;
use Data::Dumper;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $cluster_id          = $form->{cluster_id};
    my $save		        = $form->{save};

    my $cluster = $uravo->getCluster($cluster_id);
    if (!$cluster) {
        print "Location: clusters.cgi\n\n";
        exit;
    }
    my $silo = $cluster->getSilo();

    if ($save) {
        my $changelog = {user=>$user,ticket=>$form->{ticket},note=>$form->{note}};
        $cluster->update({comments=>$form->{comments}, silo_id=>$form->{silo_id}, netblock_id=>[split(/\0/, $form->{'netblock_id'})], silo_default=>(defined($form->{silo_default})?1:0)}, $changelog);

        print "Location: cluster.cgi?cluster_id=${\ $cluster->id(); }\n\n";
        exit;
    }

    print "Content-type: text/html\n\n";

    my $siloSelect = "<select name=silo_id>";
    foreach my $silo_id (sort $uravo->getSilos({id_only=>1,all_silos=>1})) {
        $siloSelect .= "<option value='$silo_id'" .(($silo_id eq $silo->id())?' selected':'') . ">$silo_id</option>\n";
    }
    $siloSelect .= "</select>";

    my %netblocks = map { $_->id()=>1 } $cluster->getNetblocks();
    my $netblockOptions = '';
    foreach my $netblock (sort $silo->getNetblocks()) {
        $netblockOptions .= "<option value=${\ $netblock->id(); }";
        $netblockOptions .= " selected" if ($netblocks{$netblock->id()});
        $netblockOptions .= ">${\ $netblock->id(); } (${\ $netblock->get('address'); })</option>\n";
    }

    print <<HEAD;
<head>
    <title>Edit Cluster: $cluster_id</title>
    <link rel=stylesheet href=/uravo.css />
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
        Cancel: function() {
          \$( this ).dialog( "close" );
        },
        "Save Changes": function() {
            \$("#note").val(\$( "#save-dialog-note").val());
            \$("#ticket").val(\$( "#save-dialog-ticket").val());
            \$( this ).dialog( "close" );
            \$( "#editcluster").submit();
        }
      }
    });
 
    \$( "#save-changes").button().click(function(e) {
        e.preventDefault();
        \$("#save-dialog").dialog("open");
    });
    \$( "#delete-cluster").button().click(function() {
            if(confirm('Are you sure you want to delete $cluster_id?')) { 
                self.location='deletecluster.cgi?cluster_id=$cluster_id';
            }
    });
});
</script>
</head>
HEAD
    print $uravo->menu();
    print <<FORM;
<div id=links>
    <ul>
        <li><a href=clusters.cgi>All Clusters</a></li>
    </ul>
</div>
<div id=content>
    <h1>${\ $cluster->id(); }</h1>
    <form method='POST' action='editcluster.cgi' id='editcluster'>
        <input type='hidden' name='cluster_id' value='$cluster_id'>
        <input type="hidden" id="ticket" name="ticket">
        <input type="hidden" id="save" name="save" value="1">
        <input type="hidden" id="note" name="note">
        <fieldset>
            <p>
                <label for=silo_id>
                    Network Silo
                    <span class=fielddesc></span>
                </label>
                $siloSelect
            </p>

            <p>
                <label for=netblock_id>
                    Netblocks
                    <span class=fielddesc></span>
                </label>
                <select name=netblock_id id=netblock_id multiple=multiple size=7>$netblockOptions</select>
            </p>
            <p>
                <label for=silo_default>
                    Silo Default
                    <span class=fielddesc>Any new servers discovered in this silo will be added to this cluster.</span>
                </label>
                <input type=checkbox name=silo_default id=silo_default ${\ ($cluster->get('silo_default')?'checked':''); }>
            </p>
            <p>
                <label for=comments>
                    Comments
                    <span class=fielddesc></span>
                </label>
                <textarea name=comments cols=50 rows=7>${\ $cluster->get('comments'); }</textarea> 
            </p>
            <p>
                <button id="save-changes">Save Changes</button>
                <button id="delete-cluster">Delete this Cluster</button>
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


