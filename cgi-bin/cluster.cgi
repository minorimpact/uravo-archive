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

    print "Content-type: text/html\n\n";
    my $cluster_id = $form->{cluster_id} || die "No cluster_id.\n";
    my $cluster = $uravo->getCluster($cluster_id) || die "Can't create cluster object.\n";
    my $silo = $cluster->getSilo();
    my $bu = $silo->getBU();

    print <<HEAD;
<head>
    <title>Cluster:$cluster_id</title>
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/jquery/jquery.dataTables-1.9.4.js" type="text/javascript"></script>

    <link rel="stylesheet" href="/uravo.css" />
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.dataTables-1.9.4.css"> 
    <script type="text/javascript">
    \$(function() {
        var anOpen = [];
        var sImageUrl = "/images/";
        var url = "API/changelog.cgi?object_id=$cluster_id&object_type=cluster";

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
                    "sDefaultContent": '<img src="'+ sImageUrl +'details_open.png">'
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
                \$('img', this).attr( 'src', sImageUrl + "details_close.png" );
                var nDetailsRow = oTable.fnOpen( nTr, fnFormatDetails(oTable, nTr), 'details' );
                \$('div.innerDetails', nDetailsRow).slideDown();
                anOpen.push( nTr );
            } else {
                \$('img', this).attr( 'src', sImageUrl+"details_open.png" );
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
                sOut = sOut + 
                    '<tr><td>'+oData.details[i].field_name+'</td><td>' + oData.details[i].old_value + '</td><td>' + oData.details[i].new_value + '</td></tr>';
            }
            sOut = sOut + '</table>'+
                '</div>';
            return sOut;
        }
    });
    </script>
</head>
HEAD

    my $serverList;
    foreach my $server_id ($cluster->getServers({id_only=>1})) {
        $serverList	.= "<li><a href=server.cgi?server_id=$server_id>$server_id</a></li>\n";
    }

    my $comments = $cluster->get('comments');
    $comments =~s/(https?:\/\/\S+)/<a href="\1" target="_new">\1<\/a>/g;

    my $netblocks;
    foreach my $netblock ($cluster->getNetblocks()) {
        my $id = $netblock->id();
        my $address = $netblock->get('address');
        $netblocks .= "<li><a href=netblock.cgi?netblock_id=$id>$id ($address)</a></li>";
    }
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href="clusters.cgi">All Clusters</a></li>
    </ul>
</div>
<div id=content>
    <h1>$cluster_id ${\ $cluster->link('default -info'); }</h1>
    <div class=field>
        <span class=label>Silo</span>
        <span class=data><a href=bu.cgi?bu_id=${\ $bu->id(); }>${\ $bu->id(); }</a></b>:<b><a href=silo.cgi?silo_id=${\ $silo->id(); }>${\ $silo->id(); }</a></span>
    </div>

    <div class=field>
        <span class=label>Netblocks</span>
        <span class=data><ol>$netblocks</ol></span>
    </div>

    <div class=field>
        <span class=label>Silo Default</span>
        <span class=data>${\ ($cluster->get('silo_default')?'Yes':'No'); }</span>
    </div>

    <div class=field>
        <span class=label>Comments</span>
        <span class=data,comments>$comments</span>
    </div>
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
            </table>
    <h2>Servers in this Cluster</h2>
    <ol>
        $serverList
    </ol>
</div>
DATA
}


