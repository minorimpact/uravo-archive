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

    my $bu_id = $form->{bu_id} || die "No bu_id.\n";
    my $bu = $uravo->getBU($bu_id) || die "Can't create bu object.\n";


    my $siloList;
    my $count = 1;
    foreach my $silo (sort { $a->id() cmp $b->id() } $uravo->getSilos({bu=>$bu_id, all_silos=>1})) {
        $siloList	.= "<tr><td colspan=2>${\ $count++; }. <a href=silo.cgi?silo_id=" . $silo->id() . ">" . $silo->id() . "</a></td></tr>\n";
    }

    my $comments = $bu->get('comments');
    $comments =~s/(https?:\/\/\S+)/<a href="\1" target="_new">\1<\/a>/g;

    print "Content-type: text/html\n\n";
    print <<HEADER;
<head>
    <title>BU: $bu_id</title>
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/jquery/jquery.dataTables-1.9.4.js" type="text/javascript"></script>

    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <link rel="stylesheet" type="text/css" href="/uravo.css"> 
    <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.dataTables-1.9.4.css"> 
    <script type="text/javascript">
    \$(function() {
        var anOpen = [];
        var sImageUrl = "/images/";
        var url = "API/changelog.cgi?object_id=$bu_id&object_type=bu";

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
HEADER

    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href="bus.cgi">All Business Units</a></li>
    </ul>
</div>
<div id=content>
    <h1>$bu_id ${\ $bu->link('default -info'); }</h1>
    <div class=field>
        <span class=label>Contact Name</span>
        <span class=data>${\ $bu->get('contact'); }</span>
    </div>
    <div class=field>
        <span class=label>Comments</span>
        <span class=data>$comments</span>
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

    <h2>Silos in this Business Unit:</h2>
    $siloList
</div>
DATA
}


