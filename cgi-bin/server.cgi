#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Netblock;
use CGI;

eval { &main(); };
print "Content-type: text/html\n\n$@\n" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $server_id = $form->{server_id} || die "No server_id.\n";

    my $server = $uravo->getServer($server_id) || die "Can't create a server object for '$server_id'\n";
    my $silo_id = $server->getSilo()->id();
    my $bu_id = $server->getSilo()->getBU()->id();
    my $cage_id = $server->getCage()->id();
    my $rack_id = $server->get('rack_id');
    my $cluster_id = $server->getCluster()->id();

    print "Content-type: text/html\n\n";
    print qq(
    <head>
        <title>Server:$server_id</title>
        <link rel="stylesheet" href="/uravo.css" />
        <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
        <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.dataTables-1.9.4.css"> 
        <script src="/js/jquery/jquery-1.9.1.js"></script>
        <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
        <script src="/js/jquery/jquery.dataTables-1.9.4.js" type="text/javascript"></script>
    </head>);
    print $uravo->menu();
    my $row = 1;
    print qq(
<div id=links>
    <a href="index.cgi">All Servers</a>
</div>
<div id=content>
    <h1>${\ $server->name(); } ${\ $server->link('default -info'); }</h1>
    Network Silo <a href="bu.cgi?bu_id=$bu_id">$bu_id</a>:<a href="silo.cgi?silo_id=$silo_id">$silo_id</a> &nbsp; &nbsp;
    Cluster <a href="cluster.cgi?cluster_id=$cluster_id">$cluster_id</a> &nbsp; &nbsp;
    Type(s) ) .
    join(",", map { "<a href='type.cgi?type_id=$_'>$_</a>" } $server->getTypes({id_only=>1})) . 
    qq(&nbsp; &nbsp;

    <div class=field>
        <span class=label>Comments</span>
        <span class=data><pre>${\ $server->get('comments'); }</pre></span>
    </div>
    
    <div class=field>
        <span class=label>Cage</span>
        <span class=data><a href="cage.cgi?cage_id=$cage_id">$cage_id</a></span>
    </div>
    <div class=field>
        <span class=label>Rack</span>
        <span class=data><a href="rack.cgi?rack_id=$rack_id">$rack_id</a></span>
    </div>
    <div class=field>
        <span class=label>Position</span>
        <span class=data>${\ $server->get('position'); }</span>
    </div>
    <div class=field>
        <span class=label>Asset Tag</span>
        <span class=data>${\ $server->get('asset_tag'); }</span>
    </div>
    <div class=field>
        <span class=label>Serial Number</span>
        <span class=data>${\ $server->get('serial_number'); }</span>
    </div>
    <div class=field>
        <span class=label>Server Model</span>
        <span class=data>${\ $server->get('server_model'); }</span>
    </div>
    <div class=field>
        <span class=label>Uravo Version</span>
        <span class=data>${\ $server->get('uravo_version'); }</span>
    </div>
    <h2>Disks</h2>
    <table>
        <tr>
            <th>Disk Name</td>
            <th>Disk Size</td>
            <th>Mounted On</td>
        </tr>);
    my $diskinfo = $server->diskinfo();
    foreach my $name (keys %$diskinfo) {
        printf("<tr><td><b>%s</b></td><td><b>%d\GB</b></td><td><b>%s</b></td></tr>\n", $name, $diskinfo->{$name}{size}, $diskinfo->{$name}{mounted_on});
    }
    print qq(
    </table>
    <h2>Interfaces</h2>
    <table>
        <tr>
            <th>Network</td>
            <th>Netblock</td>
            <th>IP</td>
            <th>MAC</td>
            <th>Name</td>
            <th>Main</td>
            <th>ICMP</td>
        </tr>);

    my @interfaces = $server->getInterfaces();
    foreach my $interface (@interfaces) {
        print "<tr>\n";
        print "<td><b>" . $interface->get('network') . "</td>\n";
        my $netblock = Uravo::Serverroles::Netblock->getNetblockFromIp($interface->get('ip'));
        if ($netblock) {
            print "<td><b><a href='netblock.cgi?netblock_id=" .$netblock->id() ."'>" . $netblock->id() . "</a></td>\n";
        } elsif ($interface->get('ip')) {
            print "<td><b>UNKNOWN</a></td>\n";
        } else {
           print "<td></td>\n";
        } 
        print "<td><b>" . $interface->get('ip') . "</td>\n";
        print "<td><b>" . $interface->get('mac') . "</td>\n";
        print "<td><b>" . $interface->get('name') . "</td>\n";
        print "<td><b>" . ($interface->get('main')?"&radic;":"") . "</td>\n";
        print "<td><b>" . ($interface->get('icmp')?"&radic;":"") . "</td>\n";
        print "</tr>\n";
        my @interface_alias = $interface->interface_alias();
        if (scalar(@interface_alias)) {
            print "<tr><td align=right>alias(es):</td><td colspan=5>" .  join(',', @interface_alias) . "</td></tr>\n";
        }
        $row++;
    }

    print qq(
    </table>
    <h2>Changelog</h2>
                        <table id="changelog">
                            <thead>
                                <tr>
                                    <th></th>
                                    <th>Date</th>
                                    <th>User</th>
                                    <th>Ticket #</th>
                                    <th>Note</th>
                                </tr>
                            </thead>
                            <tbody>
                            </tbody>
                        </table>);

    print <<FOOTER;
</div>
<script>
\$(function() {
        var anOpen = [];
        var sImageUrl = "/images";
        var url = "/cgi-bin/API/changelog.cgi?object_id=$server_id&object_type=server";

        var oTable = \$( "#changelog" ).dataTable( {
            "bProcessing": true,
            "sAjaxSource": url,
            "sAjaxDataProp": "",
            "iDisplayLength": 4,
            "fnRowCallback": function ( nRow, aData, iDisplayIndex, iDisplayIndexFull) {
                var RT = \$('td:eq(3)', nRow).html();
                if (RT != '' &&  !nRow.jira_processed) {
                    \$('td:eq(3)', nRow).html( '<a href="' + RT + '">' + RT + '</a>' );
                    nRow.jira_processed = 1;
                 }
            },
            "aoColumns": [
                {
                    "mDataProp": null,
                    "sClass": "control center",
                    "sDefaultContent": '<img src="'+ sImageUrl +'/details_open.png">'
                },
                { "mDataProp": "create_date" },
                { "mDataProp": "user" },
                { "mDataProp": "ticket" },
                { "mDataProp": "note" }
            ]
        });

        \$(document).on( 'click', '#changelog td.control', function () {
            var nTr = this.parentNode;
            var i = \$.inArray( nTr, anOpen );

            if ( i === -1 ) {
                \$('img', this).attr( 'src', sImageUrl + "/details_close.png" );
                var nDetailsRow = oTable.fnOpen( nTr, fnFormatDetails(oTable, nTr), 'details' );
                \$('div.innerDetails', nDetailsRow).slideDown();
                anOpen.push( nTr );
            } else {
                \$('img', this).attr( 'src', sImageUrl+"/details_open.png" );
                \$('div.innerDetails', \$(nTr).next()[0]).slideUp( function () {
                    oTable.fnClose( nTr );
                    anOpen.splice( i, 1 );
                });
            }
        });

        function fnFormatDetails( oTable, nTr ) {
            var oData = oTable.fnGetData( nTr );
            var sOut = '<div class="innerDetails">'+
                '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;"><tr><td><b>Field Name</b></td><td><b>Old Value</b></td><td><b>New Value</b></td></tr>';
            for (var i=0; i<oData.details.length; i++) {
                sOut = sOut + '<tr><td>'+oData.details[i].field_name+'</td><td>' + oData.details[i].old_value + '</td><td>' + oData.details[i].new_value + '</td></tr>';
            }
            sOut = sOut + '</table>' + '</div>';
            return sOut;
        }
});

</script>
FOOTER
}

