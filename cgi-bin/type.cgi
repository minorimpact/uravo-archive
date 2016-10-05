#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;
use Data::Dumper;


eval { &main(); };
print "Error: $@" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print "Content-type: text/html\n\n";
    my $type_id = $form->{type_id} || die "No type_id.\n";
    my $type = $uravo->getType($type_id) || die "Can't create type object.\n";;

    my $serverList = "<ol>\n";
    foreach my $server ($uravo->getServers({type=>$type_id, all_silos=>1, id_only=>1})) {
        $serverList     .= "<li><a href=server.cgi?server_id=$server>$server</a></li>\n";
    }
    $serverList .= "</ol>\n";

    my %proclimit = ();
    $proclimit{'>0'} = "at least one";
    $proclimit{'=0'} = "none";
    $proclimit{'=1'} = "one";
    $proclimit{'>=5'} = "at least five";
    $proclimit{'>=10'} = "at least 10";

    my $processes = $type->getProcesses();
    my $proclist;
    foreach my $proc_id (sort keys %$processes) {
        $proclist .= "<div class=field><span class=label>$processes->{$proc_id}{name}</span>";
        $proclist .= "<span class=data>$proclimit{$processes->{$proc_id}{red}}</span></div>";
    }

    my $localModuleList = join("&nbsp;", map { $_->id() . ($_->enabled($type_id)?"":"(OFF)"); } $type->getModules({remote=>0,id_only=>0}));
    my $remoteModuleList = join("&nbsp;", map { $_->id() . ($_->enabled($type_id)?"":"(OFF)"); } $type->getModules({remote=>1,id_only=>0}));

    my $comments = $type->get('comments');
    $comments =~s/(https?:\/\/\S+)/<a href="\1" target="_new">\1<\/a>/g;

    my $logFiles;
    my $logs = $type->getLogs();
    foreach my $log_id (keys %$logs) {
        my $log = $logs->{$log_id};
        $logFiles .= "$log->{log_file}:";
        foreach my $detail (@{$log->{detail}}) {
            my $regex = $detail->{regex};
            if ($regex =~/^\!(.+)$/) {
                $logFiles .= "!/$1/ ";
            } else {
                $logFiles .= "/$regex/";
            }
        }
        $logFiles .= "<br />\n";
    }

    print <<HEAD;
<head>
    <title>Type: $type_id</title>
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.dataTables-1.9.4.css"> 
    <link rel="stylesheet" type="text/css" href="/uravo.css"> 

    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/jquery/jquery.dataTables-1.9.4.js" type="text/javascript"></script>

    <script type="text/javascript">
        \$(function() {
        var anOpen = [];
        var sImageUrl = "/images/";
        var url = "API/changelog.cgi?object_id=$type_id&object_type=type";

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
    print $uravo->menu();
    print <<DATA;
<div id=links>
    <a href=types.cgi>All Types</a>
</div>
<div id=content>
    <h1>${\ $type->id(); } ${\ $type->link('default -info'); }</h1>
    <div class=field>
        <span class=label>Comments</span>
        <span class=data><pre>$comments</pre></span>
    </div>

    <div class=field>
        <span class=label>Auto ID Type</span>
        <span class=data>${\ $type->get('auto_id_type'); }</span>
    </div>

    <div class=field>
        <span class=label>Auto ID Source</span>
        <span class=data>${\ $type->get('auto_id_source'); }</span>
    </div>

    <div class=field>
        <span class=label>Auto ID Text</span>
        <span class=data>${\ $type->get('auto_id_text'); }</span>
    </div>

    <h2>Processes</h2>
    $proclist
    <h2>Local Modules</h2>
    $localModuleList
    <h2>Remote Modules</h2>
    $remoteModuleList
    <h2>Logs</h2>
    $logFiles
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
    <h2>Servers</h2>
    $serverList
</div>
DATA
}

