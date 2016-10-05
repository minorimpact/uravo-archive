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

    my $netblock_id = $form->{"netblock_id"};
    my $save = $form->{"save"};

    my $netblock = $uravo->getNetblock($netblock_id);
    if (!$netblock_id || !$netblock) {
        print "Location: netblocks.cgi\n\n";
        exit;
    }

    if ($save) {
        my $address = $form->{'address'};
        my $network = $form->{'network'};
        my $discovery = $form->{'discovery'}?1:0;
        my $silo_id = $form->{silo_id};

        my $changelog = {note=>$0, user=>$user};
        $netblock->update({address=>$address, network=>$network, discovery=>$discovery, silo_id=>$silo_id}, $changelog);
        print "Location: netblock.cgi?netblock_id=$netblock_id\n\n";
        exit;
    }

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Edit Netblock: $netblock_id</title>
    <link rel=stylesheet href=/uravo.css>
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script>
        \$(function () {
            \$( "#delete-netblock").button().click(function(e) {
                e.preventDefault();
                if(confirm('Are you sure you want to delete $netblock_id?')) { 
                    self.location='deletenetblock.cgi?netblock_id=$netblock_id';
                }
            });
        });
    </script>
</head>
HEAD
    my $siloSelect;
    if (!$netblock->get('silo_id')) { $siloSelect = "<option>--Choose a silo--</option>\n"; }
    foreach my $silo ($uravo->getSilos()) {
        $siloSelect   .= "<option value='$silo->{silo_id}'";
        $siloSelect   .= " selected" if ($silo->id() eq $netblock->get('silo_id'));
        $siloSelect   .= ">$silo->{silo_id}</option>\n";
    }

    my $networkSelect;
    if (!$netblock->get('network')) { $networkSelect = "<option>--Choose a network--</option>\n"; }
    foreach my $network ($uravo->getNetworks()) {
        $networkSelect   .= "<option value='$network->{network}'";
        $networkSelect   .= " selected" if ($network->{network} eq $netblock->get('network'));
        $networkSelect   .= ">$network->{network}</option>\n";
    }

    print $uravo->menu();
     
    print qq(<br><br>
<div id=links>
    <ul>
        <li><a href=netblocks.cgi>All Netblocks</a></li>
    </ol>
</div>
<div id=content>
    <h1>$netblock_id</h1>
    <form method='POST'>
        <input type=hidden name=netblock_id value='$netblock_id'>
        <fieldset>
            <p>
                <label for=address>
                    Address
                    <span class=fielddesc></span>
                </label>
                <input type="text" name="address" value="${\ $netblock->get("address"); }" maxlength="18" />
            </p>

            <p>
                <label for=silo_id>
                    Silo
                    <span class=fielddesc></span>
                </label>
                <select name="silo_id">$siloSelect</select>
            </p>

            <p>
                <label for=network>
                    Network
                    <span class=fielddesc></span>
                </label>
                <select name="network">$networkSelect</select>
            </p>

            <p>
                <label for=discovery>
                    Include in discovery
                    <span class=fielddesc></span>
                </label>
                <input type=checkbox name=discovery ${\ ($netblock->get('discovery')?'checked':''); }>
            </p>

            <p>
                <button name=save id=save-changes value=1>Save Changes</button>
                <button id=delete-netblock>Delete this Netblock</button>
            </p>
        </fieldset>
    </form>
</div>);

}

